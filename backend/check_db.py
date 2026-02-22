import sqlite3
try:
    conn = sqlite3.connect('dailyprompt.db')
    cur = conn.cursor()
    cur.execute('SELECT count(*) FROM prompts')
    print(f"Prompts count: {cur.fetchone()[0]}")
    cur.execute('SELECT * FROM app_state')
    print(f"App State: {cur.fetchall()}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
