import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
import logging

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, Prompt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "https://prompts.chat/api/prompts?page={page}&perPage=50"

def fetch_page(page):
    """Fetch a single page of prompts from prompts.chat."""
    url = API_URL.format(page=page)
    req = urllib.request.Request(url, headers={'User-Agent': 'DailyPrompt/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        logger.error(f"Error fetching page {page}: {e}")
        return None

def sync_prompts():
    """Sync prompts from the API to the local database."""
    app = create_app()
    with app.app_context():
        # Get start page
        page = 1
        total_synced = 0
        total_skipped = 0
        
        while True:
            logger.info(f"Fetching page {page}...")
            data = fetch_page(page)
            
            if not data or not data.get("prompts"):
                logger.info("No more prompts found or API error. Stopping.")
                break
            
            prompts_list = data["prompts"]
            inserted = 0
            skipped = 0
            
            for item in prompts_list:
                slug = item.get("slug")
                if not slug:
                    continue
                
                # Check if prompt already exists by source_slug
                existing = Prompt.query.filter_by(source_slug=slug).first()
                if existing:
                    skipped += 1
                    continue
                
                category_name = "general"
                if item.get("category") and item["category"].get("name"):
                    category_name = item["category"]["name"]
                
                new_prompt = Prompt(
                    title=item.get("title", "Untitled"),
                    description=item.get("description", ""),
                    prompt_body=item.get("content", ""),
                    system_prompt="", # API doesn't seem to explicitly separate this
                    category=category_name,
                    source_slug=slug,
                    source_url=f"https://prompts.chat/prompt/{slug}"
                )
                
                db.session.add(new_prompt)
                inserted += 1
            
            if inserted > 0:
                try:
                    db.session.commit()
                    logger.info(f"Page {page}: Inserted {inserted}, Skipped {skipped} (already exist)")
                    total_synced += inserted
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Database error on page {page}: {e}")
            else:
                logger.info(f"Page {page}: All {skipped} prompts already exist.")
            
            total_skipped += skipped
            
            # Check if we've reached the last page
            if page >= data.get("totalPages", page):
                break
                
            page += 1
            
        logger.info(f"Sync complete. Total new prompts added: {total_synced}. Total skipped (already exist): {total_skipped}.")

if __name__ == "__main__":
    logger.info("Starting prompts.chat sync process...")
    sync_prompts()
