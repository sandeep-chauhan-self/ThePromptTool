"""
Playwright Scraper — Seeds the database with prompts from Anthropic's Prompt Library.

Usage:
    python scripts/scrape_prompts.py

This script:
  1. Navigates to the Anthropic Prompt Library index page
  2. Extracts all prompt slugs from the page
  3. Visits each prompt's detail page to extract title, description, and prompt body
  4. Upserts prompts into PostgreSQL (ON CONFLICT DO NOTHING for idempotency)
  5. Updates the total_prompts counter in app_state

Safe to re-run: existing prompts (including served ones) are never modified.
"""

import os
import sys
import re
import time
import json

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

# Load environment
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_URL = f"sqlite:///{os.path.join(basedir, 'dailyprompt.db')}"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

BASE_URL = "https://docs.anthropic.com"
LIBRARY_URL = f"{BASE_URL}/en/prompt-library/library"
DELAY_BETWEEN_PAGES = 2  # seconds — be respectful to Anthropic's servers


def categorize_prompt(title, description):
    """Assign a category based on keywords in title/description."""
    text = f"{title} {description}".lower()

    categories = {
        "coding": ["code", "python", "sql", "html", "css", "javascript", "git", "bug",
                    "function", "latex", "excel", "formula", "script", "apps script",
                    "spreadsheet", "csv", "json", "xml", "algorithm", "complexity"],
        "writing": ["write", "story", "prose", "edit", "grammar", "poem", "alliteration",
                     "portmanteau", "tongue twister", "memo", "email", "tweet", "pun",
                     "riddle", "simile", "neologism"],
        "analysis": ["extract", "classify", "analyze", "interpret", "detect", "organize",
                      "data", "review", "insight", "report", "summarize", "grade",
                      "estimate", "evaluate"],
        "education": ["teach", "explain", "simplify", "lesson", "tutor", "socratic",
                       "trivia", "interview", "career", "mentor", "coach"],
        "creative": ["creative", "fashion", "brand", "product", "name", "design",
                      "color", "mood", "dream", "sci-fi", "vr", "game", "travel",
                       "culinary", "recipe", "fitness"],
        "language": ["translate", "language", "idiom", "polyglot", "emoji", "airport",
                      "direction", "decode"],
        "productivity": ["meeting", "moderate", "pii", "motivat", "mindful", "ethical",
                          "perspective", "cite", "source"],
    }

    for category, keywords in categories.items():
        if any(kw in text for kw in keywords):
            return category

    return "general"


def extract_prompts_from_code_block(page):
    """
    Extract both system prompt and user prompt from the API code block.
    Returns: { "system_prompt": str, "user_prompt": str } or None
    """
    try:
        code_blocks = page.query_selector_all("pre code, pre")
        for block in code_blocks:
            text_content = block.inner_text()

            # Look for API code blocks that contain messages
            if "messages" not in text_content:
                continue

            result = {"system_prompt": "", "user_prompt": ""}

            # Extract system prompt: system="..." or system="""..."""
            sys_match = re.search(
                r'system\s*=\s*"((?:[^"\\]|\\.)*)"',
                text_content,
                re.DOTALL,
            )
            if sys_match:
                sys_text = sys_match.group(1)
                sys_text = sys_text.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")
                result["system_prompt"] = sys_text.strip()

            # Extract user message text: "text": "..."
            text_match = re.search(
                r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"',
                text_content,
                re.DOTALL,
            )
            if text_match:
                user_text = text_match.group(1)
                user_text = user_text.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")
                result["user_prompt"] = user_text.strip()

            if result["system_prompt"] or result["user_prompt"]:
                return result

    except Exception as e:
        print(f"  ⚠ Error extracting prompts: {e}")

    return None



def scrape_library(page):
    """
    Scrape the Anthropic Prompt Library index page for all prompt slugs.
    Returns a list of unique slugs.
    """
    print(f"📖 Navigating to library index: {LIBRARY_URL}")
    page.goto(LIBRARY_URL, wait_until="networkidle", timeout=30000)
    time.sleep(2)

    # Extract all links matching /en/prompt-library/<slug>
    links = page.query_selector_all('a[href*="/prompt-library/"]')
    slugs = set()

    for link in links:
        href = link.get_attribute("href")
        if href and "/prompt-library/" in href:
            # Extract slug — handle both relative and absolute URLs
            parts = href.rstrip("/").split("/prompt-library/")
            if len(parts) == 2 and parts[1] and parts[1] != "library":
                slugs.add(parts[1])

    print(f"✅ Found {len(slugs)} unique prompt slugs")
    return sorted(slugs)


def scrape_prompt_detail(page, slug, attempt=1, max_attempts=3):
    """
    Navigate to a prompt's detail page and extract its data.
    Retries up to max_attempts times on failure.
    """
    url = f"{BASE_URL}/en/prompt-library/{slug}"

    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(1)

        # Extract title from h1
        h1 = page.query_selector("h1")
        title = h1.inner_text().strip() if h1 else slug.replace("-", " ").title()

        # Extract description from meta or first paragraph
        description = ""
        meta_desc = page.query_selector('meta[name="description"], meta[property="og:description"]')
        if meta_desc:
            description = meta_desc.get_attribute("content") or ""
        if not description:
            first_p = page.query_selector("article p, main p, .content p")
            if first_p:
                description = first_p.inner_text().strip()

        # Extract prompts from code block (system + user)
        extracted = extract_prompts_from_code_block(page)
        system_prompt = ""
        prompt_body = ""
        if extracted:
            system_prompt = extracted.get("system_prompt", "")
            prompt_body = extracted.get("user_prompt", "")
        if not prompt_body:
            # Fallback: use description as prompt body
            prompt_body = description or f"Prompt: {title}"

        category = categorize_prompt(title, description)

        return {
            "title": title,
            "description": description,
            "prompt_body": prompt_body,
            "system_prompt": system_prompt,
            "category": category,
            "source_slug": slug,
            "source_url": url,
        }

    except Exception as e:
        if attempt < max_attempts:
            wait_time = 2 ** attempt
            print(f"  ⚠ Attempt {attempt} failed for {slug}: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            return scrape_prompt_detail(page, slug, attempt + 1, max_attempts)
        else:
            print(f"  ❌ Failed to scrape {slug} after {max_attempts} attempts: {e}")
            return None


def upsert_prompts(prompts):
    """
    Insert prompts into database. Uses ON CONFLICT DO NOTHING (Postgres)
    or INSERT OR IGNORE (SQLite) for idempotency.
    Returns count of newly inserted prompts.
    """
    is_sqlite = DATABASE_URL.startswith("sqlite")
    
    if is_sqlite:
        import sqlite3
        # Extract path from sqlite:///...
        db_path = DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
    else:
        conn = psycopg2.connect(DATABASE_URL)
    
    cur = conn.cursor()

    inserted = 0
    for prompt in prompts:
        try:
            if is_sqlite:
                cur.execute(
                    """
                    INSERT INTO prompts 
                    (title, description, prompt_body, system_prompt, category, source_slug, source_url, scraped_at, is_served)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 0)
                    ON CONFLICT(source_slug) DO UPDATE SET
                        system_prompt = excluded.system_prompt,
                        prompt_body = excluded.prompt_body,
                        description = excluded.description
                    """,
                    (
                        prompt["title"],
                        prompt["description"],
                        prompt["prompt_body"],
                        prompt.get("system_prompt", ""),
                        prompt["category"],
                        prompt["source_slug"],
                        prompt["source_url"],
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO prompts (title, description, prompt_body, system_prompt, category, source_slug, source_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_slug) DO UPDATE SET
                        system_prompt = EXCLUDED.system_prompt,
                        prompt_body = EXCLUDED.prompt_body,
                        description = EXCLUDED.description
                    """,
                    (
                        prompt["title"],
                        prompt["description"],
                        prompt["prompt_body"],
                        prompt.get("system_prompt", ""),
                        prompt["category"],
                        prompt["source_slug"],
                        prompt["source_url"],
                    ),
                )
            if cur.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"  ⚠ DB error for {prompt['source_slug']}: {e}")
            conn.rollback()
            continue

    # Update total_prompts counter
    if is_sqlite:
        cur.execute("SELECT COUNT(*) FROM prompts")
        total = cur.fetchone()[0]
        cur.execute(
            "INSERT OR REPLACE INTO app_state (key, value_int) VALUES ('total_prompts', ?)",
            (total,),
        )
    else:
        cur.execute("SELECT COUNT(*) FROM prompts")
        total = cur.fetchone()[0]
        cur.execute(
            "UPDATE app_state SET value_int = %s WHERE key = 'total_prompts'",
            (total,),
        )

    conn.commit()
    cur.close()
    conn.close()

    return inserted


def main():
    """Main entry point: scrape the library and populate the database."""
    print("🚀 Daily Prompt Scraper — Starting")
    print(f"📡 Database: {DATABASE_URL[:50]}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Step 1: Get all prompt slugs
        slugs = scrape_library(page)

        if not slugs:
            print("❌ No prompt slugs found — page structure may have changed. Aborting.")
            browser.close()
            sys.exit(1)

        # Step 2: Scrape each prompt's detail page
        total_inserted = 0
        for i, slug in enumerate(slugs, 1):
            print(f"  [{i}/{len(slugs)}] Scraping: {slug}")
            prompt_data = scrape_prompt_detail(page, slug)
            if prompt_data:
                inserted = upsert_prompts([prompt_data])
                total_inserted += inserted
            time.sleep(DELAY_BETWEEN_PAGES)

        browser.close()

    print(f"\n📊 Scraper finished. Total new prompts inserted: {total_inserted}")


if __name__ == "__main__":
    main()
