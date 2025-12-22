import sqlite3
import httpx
import asyncio
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()
API_KEY = os.getenv("TRELLO_API_KEY")
DB_FILE = "sql_app.db"
USER_ID = 1

def get_token():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT access_token FROM integration WHERE user_id = ? AND provider = 'trello'",
            (USER_ID,)
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        return None
    except Exception as e:
        print(f"[ERROR] Error reading DB: {e}")
        return None

async def debug_trello():
    if not API_KEY:
        print("[ERROR] TRELLO_API_KEY not found in .env file.")
        return

    token = get_token()
    if not token:
        print("[ERROR] No Trello token found for user 1 in the database.")
        return

    print(f"[OK] Found API Key: {API_KEY[:4]}...{API_KEY[-4:]}")
    print(f"[OK] Found Token:   {token[:4]}...{token[-4:]}")
    
    url = "https://api.trello.com/1/members/me/boards"
    params = {
        "key": API_KEY,
        "token": token
    }

    async with httpx.AsyncClient() as client:
        print("\n1. Testing Connection (Get Boards)...")
        resp = await client.get(url, params=params)
        
        if resp.status_code == 200:
            print("   [SUCCESS] Connection Successful!")
            boards = resp.json()
            print(f"   Found {len(boards)} boards.")
            if boards:
                print(f"   First board: {boards[0].get('name')}")
        else:
            print(f"   [FAILED] Status: {resp.status_code}")
            print(f"   Response: {resp.text}")

if __name__ == "__main__":
    asyncio.run(debug_trello())

