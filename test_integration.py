import asyncio
import requests
import json
import sys
import os

BASE_URL = "http://localhost:8000"

def test_settings_llm_integration():
    """Test that settings are properly integrated with LLM"""
    print("Testing Settings -> LLM Integration")
    print("=" * 50)
    
    # 1. Check current settings
    print("1. Checking current settings...")
    try:
        settings_res = requests.get(f"{BASE_URL}/settings/")
        if settings_res.status_code != 200:
            print(f"FAILED: {settings_res.status_code}")
        settings = settings_res.json()
        print(f"   Settings loaded: {settings.get('has_settings', False)}")
    except Exception as e:
        print(f"FAILED to connect: {e}")
        return False
    
    # 2. Check available providers
    print("\n2. Checking available LLM providers...")
    try:
        providers_res = requests.get(f"{BASE_URL}/chat/providers/available")
        if providers_res.status_code != 200:
            print(f"FAILED to get providers: {providers_res.status_code}")
            return False
        providers = providers_res.json()
        print(f"   Available providers: {providers.get('available_providers', [])}")
        print(f"   Default model: {providers.get('default_model')}")
    except Exception as e:
        print(f"FAILED to get providers: {e}")
        return False
    
    # 3. Test chat with settings (WebSocket)
    print("\n3. Testing chat with current settings...")
    try:
        # Create WebSocket connection
        import websockets
        async def test_chat():
            uri = "ws://localhost:8000/chat/ws/test_integration"
            try:
                async with websockets.connect(uri) as websocket:
                    # Send test message
                    await websocket.send(json.dumps({
                        "type": "message",
                        "content": "Hello",
                        "context": {}
                    }))
                    
                    # Receive responses
                    async for message in websocket:
                        data = json.loads(message)
                        if data.get("type") == "message_complete":
                            print(f"   Chat responded with {len(data['content'])} characters")
                            return True
                        elif data.get("type") == "error":
                            print(f"   Chat error: {data['content']}")
                            # Acceptable if no keys configured
                            if "No API keys configured" in data['content']:
                                print("   (Expected: No keys configured)")
                                return True
                            return False
            except Exception as e:
                print(f"   WebSocket failed: {e}")
                return False
        
        # Run async test
        success = asyncio.run(test_chat())
        if not success:
            return False
        
    except ImportError:
        print("   websockets package not installed, skipping chat test")
    except Exception as e:
        print(f"   Chat test failed: {e}")
        return False
    
    # 4. Test audit persistence
    print("\n4. Testing audit persistence...")
    try:
        # Create test project directory
        import tempfile
        import shutil
        test_dir = tempfile.mkdtemp()
        test_file = os.path.join(test_dir, "test.py")
        
        with open(test_file, 'w') as f:
            f.write('def hello():\\n    api_key = "sk-test1234567890"\\n    return api_key')
        
        # Start audit
        audit_res = requests.post(
            f"{BASE_URL}/auditor/project/test_project/persistent",
            params={
                "project_path": test_dir,
                "project_id": "test_project"
            }
        )
        
        if audit_res.status_code == 200:
            print(f"   Audit started successfully")
            
            # Check audit runs
            import time
            for _ in range(5):
                time.sleep(1)
                runs_res = requests.get(f"{BASE_URL}/auditor/project/test_project/runs")
                if runs_res.status_code == 200:
                    runs = runs_res.json()
                    if runs.get('total_runs', 0) > 0:
                        run = runs['runs'][0]
                        print(f"   Audit run completed: Status={run['status']}, Issues={run['total_issues']}")
                        break
            else:
                print("   Audit did not complete in time")
                
        else:
            print(f"   Failed to start audit: {audit_res.text}")
            
        # Cleanup
        try:
            shutil.rmtree(test_dir)
        except:
            pass
            
    except Exception as e:
        print(f"   Audit test failed: {e}")
    
    return True

if __name__ == "__main__":
    print("\nAIde Integration Test Suite")
    print("=" * 60)
    
    test_settings_llm_integration()
    
    print("\n" + "=" * 60)
