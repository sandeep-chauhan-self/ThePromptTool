import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os

PG_URL = "postgresql://postgres:yaQhkPrqzhwhhVImNTFYcdhSHROrMvWp@gondola.proxy.rlwy.net:16452/railway"

def migrate():
    print("Connecting to local SQLite...")
    basedir = os.path.dirname(os.path.abspath(__file__))
    sqlite_db_path = os.path.join(basedir, "dailyprompt.db")
    
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    print("Connecting to remote PostgreSQL...")
    pg_conn = psycopg2.connect(PG_URL)
    pg_cur = pg_conn.cursor()

    # 1. Prompts
    sqlite_cur.execute("SELECT * FROM prompts")
    prompts = [dict(row) for row in sqlite_cur.fetchall()]
    print(f"Loaded {len(prompts)} prompts from SQLite.")

    if prompts:
        cols = list(prompts[0].keys())
        values = []
        for p in prompts:
            row = []
            for col in cols:
                val = p[col]
                if col == "is_served":
                    val = bool(val)
                row.append(val)
            values.append(row)
            
        insert_query = f"""
            INSERT INTO prompts ({', '.join(cols)})
            VALUES %s
            ON CONFLICT (source_slug) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                prompt_body = EXCLUDED.prompt_body,
                system_prompt = EXCLUDED.system_prompt,
                category = EXCLUDED.category,
                source_url = EXCLUDED.source_url
        """
        execute_values(pg_cur, insert_query, values)
        print("Inserted/Updated prompts in PostgreSQL (Deduped by source_slug).")

    # 2. App State
    sqlite_cur.execute("SELECT * FROM app_state")
    app_states = [dict(row) for row in sqlite_cur.fetchall()]
    
    if app_states:
        cols = list(app_states[0].keys())
        values = [[a[col] for col in cols] for a in app_states]
        
        insert_query = f"""
            INSERT INTO app_state ({', '.join(cols)})
            VALUES %s
            ON CONFLICT (key) DO UPDATE SET
                value_int = EXCLUDED.value_int
        """
        execute_values(pg_cur, insert_query, values)
        print("Inserted/Updated app_state in PostgreSQL.")

    # 3. Serve Log
    try:
        sqlite_cur.execute("SELECT * FROM serve_log")
        serve_logs = [dict(row) for row in sqlite_cur.fetchall()]
        
        if serve_logs:
            cols = list(serve_logs[0].keys())
            values = [[s[col] for col in cols] for s in serve_logs]
            
            insert_query = f"""
                INSERT INTO serve_log ({', '.join(cols)})
                VALUES %s
                ON CONFLICT (id) DO NOTHING
            """
            execute_values(pg_cur, insert_query, values)
            print("Inserted serve_log records in PostgreSQL.")
    except sqlite3.OperationalError:
        print("No serve_log table found in SQLite.")

    # Commit and close
    pg_conn.commit()
    
    # Update Sequences
    try:
        pg_cur.execute("SELECT setval('prompts_id_seq', (SELECT MAX(id) FROM prompts));")
        pg_cur.execute("SELECT setval('serve_log_id_seq', (SELECT COALESCE(MAX(id), 1) FROM serve_log));")
        pg_conn.commit()
        print("Sequences updated.")
    except Exception as e:
        print("Warning: Could not update sequences:", e)
        pg_conn.rollback()

    pg_cur.close()
    pg_conn.close()
    sqlite_conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
