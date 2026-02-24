import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

PG_URL = os.getenv("DATABASE_URL")
if not PG_URL:
    PG_URL = "postgresql://postgres:yaQhkPrqzhwhhVImNTFYcdhSHROrMvWp@gondola.proxy.rlwy.net:16452/railway"

try:
    conn = psycopg2.connect(PG_URL)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM prompts')
    count = cur.fetchone()[0]
    print(f"Total prompts in Railway Database: {count}")
    
    cur.execute('SELECT COUNT(*) FROM prompts WHERE source_url = "user-submission"')
    # Wait, source_url should be compared to 'user-submission'
    cur.execute("SELECT COUNT(*) FROM prompts WHERE source_url = 'user-submission'")
    custom_count = cur.fetchone()[0]
    print(f"User submitted prompts: {custom_count}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
