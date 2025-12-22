import sqlite3
import httpx
import asyncio

# Configuration
DB_FILE = "sql_app.db"
FILE_KEY = "aip5DnnlE3lPeYbc3ttHAF"
USER_ID = 1

def get_token():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT access_token FROM integration WHERE user_id = ? AND provider = 'figma'",
            (USER_ID,)
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        return None
    except Exception as e:
        print(f"Error reading DB: {e}")
        return None

async def debug_figma():
    token = get_token()
    if not token:
        print("[ERROR] No Figma token found for user 1 in the database.")
        return

    print(f"[OK] Found Token: {token[:4]}...{token[-4:]}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # 1. Check Identity
        print("\n1. Checking Token Identity (/v1/me)...")
        resp_me = await client.get("https://api.figma.com/v1/me", headers=headers)
        if resp_me.status_code == 200:
            user_data = resp_me.json()
            print(f"   [SUCCESS] Authenticated as: {user_data.get('handle')} ({user_data.get('email')})")
        else:
            print(f"   [FAILED] Auth Failed: {resp_me.status_code}")
            print(f"   Response: {resp_me.text}")
            return # Stop if auth fails

        # 2. Check File Access
        print(f"\n2. Checking File Access (/v1/files/{FILE_KEY})...")
        resp_file = await client.get(f"https://api.figma.com/v1/files/{FILE_KEY}", headers=headers)
        
        if resp_file.status_code == 200:
            print("   [SUCCESS] File access successful!")
            data = resp_file.json()
            print(f"   File Name: {data.get('name')}")
        else:
            print(f"   [FAILED] Access Failed: {resp_file.status_code}")
            print(f"   Reason: {resp_file.text}")

if __name__ == "__main__":
    asyncio.run(debug_figma())

