import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app.sandbox.service import SandboxService

async def test_sandbox_lifecycle():
    print("--- Starting Sandbox Lifecycle Test ---")
    service = SandboxService()
    
    # 1. Create Sandbox
    print("\n1. Creating Sandbox (Node:18)...")
    try:
        result = service.create_sandbox(user_id=999, image="node:18")
        container_id = result["container_id"]
        print(f"   Success! Container ID: {container_id[:12]}...")
    except Exception as e:
        print(f"   Failed to create sandbox: {e}")
        return

    try:
        # 2. Write File
        print("\n2. Writing 'hello.js'...")
        js_code = "console.log('Hello from inside the sandbox!');"
        service.write_file(container_id, "hello.js", js_code)
        print("   File written.")

        # 3. Execute Command
        print("\n3. Executing 'node hello.js'...")
        exec_result = service.execute_command(container_id, "node hello.js")
        print(f"   Output: {exec_result['output'].strip()}")
        if "Hello from inside the sandbox!" in exec_result['output']:
            print("   Verification: SUCCESS")
        else:
            print("   Verification: FAILED")

        # 4. Git Check (Mock)
        print("\n4. Checking Git Version...")
        git_result = service.execute_command(container_id, "git --version")
        print(f"   Git Version: {git_result['output'].strip()}")

    finally:
        # 5. Cleanup
        print("\n5. Cleaning up...")
        service.stop_sandbox(container_id)
        print("   Sandbox stopped and removed.")
        print("\n--- Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_sandbox_lifecycle())

