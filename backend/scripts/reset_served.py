"""
Dev utility: Reset all served prompts back to unserved state.

Usage:
    python scripts/reset_served.py

WARNING: This is destructive — only use in development!
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/dailyprompt")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Reset all prompts
    cur.execute("UPDATE prompts SET is_served = FALSE, served_at = NULL, serve_order = NULL")
    reset_count = cur.rowcount

    # Reset counter
    cur.execute("UPDATE app_state SET value_int = 0 WHERE key = 'serve_counter'")

    # Clear serve log
    cur.execute("DELETE FROM serve_log")
    log_count = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Reset {reset_count} prompts to unserved")
    print(f"🗑️  Deleted {log_count} serve log entries")
    print(f"🔄 Counter reset to 0")


if __name__ == "__main__":
    confirm = input("⚠ This will reset ALL served prompts. Type 'yes' to confirm: ")
    if confirm.lower() == "yes":
        main()
    else:
        print("Aborted.")
