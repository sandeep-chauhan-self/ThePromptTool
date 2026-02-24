import os
import sys
from datetime import datetime, timezone

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import create_app
from models import db, Prompt, AppState
from services.prompt_service import serve_next_prompt
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("--- VERIFYING PROMPT LOOPING ---")
    
    # 1. Count current state
    total = db.session.query(Prompt).count()
    unserved_count = db.session.query(Prompt).filter_by(is_served=False).count()
    print(f"Total: {total}, Unserved: {unserved_count}")
    
    # 2. Mark ALL as served for a forced reset test
    print("Forcing exhaustion (marking all as served)...")
    db.session.execute(text("UPDATE prompts SET is_served = TRUE"))
    db.session.commit()
    
    # 3. Call serve_next_prompt
    # This should trigger the reset and then return a prompt
    print("Calling serve_next_prompt (should trigger reset)...")
    prompt = serve_next_prompt(client_ip="127.0.0.1")
    
    if prompt:
        print(f"Success! Served: {prompt['title']}")
        print(f"Stats after reset: {prompt['stats']}")
        
        # Verify unserved count is now Total - 1
        new_unserved = db.session.query(Prompt).filter_by(is_served=False).count()
        print(f"Unserved count now: {new_unserved}")
        
        if new_unserved == total - 1:
            print("LOOPING VERIFIED SUCCESSFULLY")
        else:
            print(f"VERIFICATION FAILED: Expected {total - 1} unserved, got {new_unserved}")
    else:
        print("VERIFICATION FAILED: serve_next_prompt returned None")
