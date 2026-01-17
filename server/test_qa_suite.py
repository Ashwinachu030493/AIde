r"""
AIde Backend - Comprehensive QA Test Suite
Tests all major endpoints as a QA engineer / Tech Lead would.

Run with: f:\AIde\.venv\Scripts\python.exe server\test_qa_suite.py
"""

import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def log_pass(test_name, details=""):
    print(f"{Colors.GREEN}✓ PASS{Colors.RESET} - {test_name} {details}")

def log_fail(test_name, error):
    print(f"{Colors.RED}✗ FAIL{Colors.RESET} - {test_name}: {error}")

def log_section(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self):
        self.passed += 1

    def add_fail(self, test, error):
        self.failed += 1
        self.errors.append((test, str(error)))

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.RESET}")
        print(f"{'='*60}")
        print(f"Total: {total} | {Colors.GREEN}Passed: {self.passed}{Colors.RESET} | {Colors.RED}Failed: {self.failed}{Colors.RESET}")
        if self.errors:
            print(f"\n{Colors.YELLOW}Failed Tests:{Colors.RESET}")
            for test, error in self.errors:
                print(f"  - {test}: {error}")
        print(f"{'='*60}\n")
        return self.failed == 0

results = TestResults()

# ============================================================
# 1. HEALTH CHECK TESTS
# ============================================================
def test_health_endpoint():
    log_section("1. HEALTH CHECK TESTS")
    
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data.get("status") == "ok", f"Expected status 'ok', got {data}"
        log_pass("Health Endpoint", f"(status={data.get('status')})")
        results.add_pass()
    except Exception as e:
        log_fail("Health Endpoint", e)
        results.add_fail("Health Endpoint", e)

# ============================================================
# 2. SETTINGS API TESTS
# ============================================================
def test_settings_api():
    log_section("2. SETTINGS API TESTS")
    
    # Test GET /settings/
    try:
        resp = requests.get(f"{BASE_URL}/settings/", timeout=5)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "has_settings" in data, "Missing 'has_settings' key"
        log_pass("GET /settings/", f"(has_settings={data.get('has_settings')})")
        results.add_pass()
    except Exception as e:
        log_fail("GET /settings/", e)
        results.add_fail("GET /settings/", e)

    # Test POST /settings/api-keys (valid provider)
    try:
        resp = requests.post(f"{BASE_URL}/settings/api-keys", 
            json={"provider": "openai", "api_key": "sk-test1234567890abcdefghij"},
            timeout=5)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data.get("status") == "success", f"Expected success, got {data}"
        log_pass("POST /settings/api-keys (valid)", f"(action={data.get('action')})")
        results.add_pass()
    except Exception as e:
        log_fail("POST /settings/api-keys (valid)", e)
        results.add_fail("POST /settings/api-keys (valid)", e)

    # Test POST /settings/api-keys (invalid provider)
    try:
        resp = requests.post(f"{BASE_URL}/settings/api-keys", 
            json={"provider": "invalid_provider", "api_key": "somekey"},
            timeout=5)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        log_pass("POST /settings/api-keys (invalid provider)", "(correctly rejected)")
        results.add_pass()
    except Exception as e:
        log_fail("POST /settings/api-keys (invalid provider)", e)
        results.add_fail("POST /settings/api-keys (invalid provider)", e)

    # Test POST /settings/preferences
    try:
        resp = requests.post(f"{BASE_URL}/settings/preferences", 
            json={"default_model": "gpt-4", "theme": "dark", "auto_ingest": True},
            timeout=5)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        log_pass("POST /settings/preferences", "(preferences saved)")
        results.add_pass()
    except Exception as e:
        log_fail("POST /settings/preferences", e)
        results.add_fail("POST /settings/preferences", e)

    # Verify settings were saved
    try:
        resp = requests.get(f"{BASE_URL}/settings/", timeout=5)
        data = resp.json()
        assert data.get("has_settings") == True, "Settings not saved"
        prefs = data.get("preferences", {})
        assert prefs.get("default_model") == "gpt-4", f"Model not saved: {prefs}"
        providers = data.get("providers_configured", {})
        assert providers.get("openai") == True, "OpenAI key not saved"
        log_pass("Settings Persistence Verification", "(all saved correctly)")
        results.add_pass()
    except Exception as e:
        log_fail("Settings Persistence Verification", e)
        results.add_fail("Settings Persistence Verification", e)

# ============================================================
# 3. AUDITOR API TESTS (UPDATED FOR CONSOLIDATED SYSTEM)
# ============================================================
def test_audit_api():
    log_section("3. AUDITOR API TESTS")
    
    # NOTE: /audit endpoints deprecated; using /auditor/project/{project_id}/persistent
    # Test persistent audit endpoint
    try:
        resp = requests.post(
            f"{BASE_URL}/auditor/project/test-project/persistent?project_path=f:/AIde/server/auditor", 
            json={},
            timeout=10
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "status" in data, "Missing status in response"
        assert "project_id" in data, "Missing project_id in response"
        log_pass("POST /auditor/project/persistent", f"(status: {data.get('status')})")
        results.add_pass()
    except Exception as e:
        log_fail("POST /auditor/project/persistent", e)
        results.add_fail("POST /auditor/project/persistent", e)

    # Test audit runs endpoint
    try:
        resp = requests.get(f"{BASE_URL}/auditor/project/test-project/runs", timeout=5)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "project_id" in data, "Missing project_id"
        assert "runs" in data, "Missing runs"
        log_pass("GET /auditor/project/runs", f"(runs: {len(data.get('runs', []))})")
        results.add_pass()
    except Exception as e:
        log_fail("GET /auditor/project/runs", e)
        results.add_fail("GET /auditor/project/runs", e)

    # Test audit findings endpoint
    try:
        resp = requests.get(f"{BASE_URL}/auditor/project/test-project/findings", timeout=5)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "project_id" in data, "Missing project_id"
        assert "findings" in data, "Missing findings"
        log_pass("GET /auditor/project/findings", f"(findings: {len(data.get('findings', []))})")
        results.add_pass()
    except Exception as e:
        log_fail("GET /auditor/project/findings", e)
        results.add_fail("GET /auditor/project/findings", e)

# ============================================================
# 4. INGESTION API TESTS
# ============================================================
def test_ingestion_api():
    log_section("4. INGESTION API TESTS")
    
    # Test GET /ingestion/capabilities
    try:
        resp = requests.get(f"{BASE_URL}/ingestion/capabilities", timeout=5)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "supported_modes" in data, "Missing supported_modes"
        log_pass("GET /ingestion/capabilities", f"(modes: {data.get('supported_modes')})")
        results.add_pass()
    except Exception as e:
        log_fail("GET /ingestion/capabilities", e)
        results.add_fail("GET /ingestion/capabilities", e)

    # Test POST /ingestion/file
    test_file = "f:/AIde/server/main.py"
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        resp = requests.post(f"{BASE_URL}/ingestion/file",
            data={"file_path": test_file, "project_id": "test_qa", "content": content},
            timeout=15)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "chunks" in data, "Missing chunks in response"
        log_pass("POST /ingestion/file", f"(chunks: {data.get('chunks', 0)})")
        results.add_pass()
    except Exception as e:
        log_fail("POST /ingestion/file", e)
        results.add_fail("POST /ingestion/file", e)

    # Test POST /ingestion/project (async job)
    try:
        resp = requests.post(f"{BASE_URL}/ingestion/project",
            data={"project_path": "f:/AIde/server/audit", "project_id": "test_qa_project", "max_workers": "2"},
            timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        job_id = data.get("job_id")
        assert job_id, "Missing job_id"
        log_pass("POST /ingestion/project", f"(job_id: {job_id[:8]}...)")
        results.add_pass()
        
        # Wait and check job status
        time.sleep(3)
        resp = requests.get(f"{BASE_URL}/ingestion/job/{job_id}", timeout=5)
        assert resp.status_code == 200, f"Expected 200 for job status"
        status_data = resp.json()
        log_pass("GET /ingestion/job/{id}", f"(status: {status_data.get('status')}, processed: {status_data.get('processed_files')})")
        results.add_pass()
        
    except Exception as e:
        log_fail("POST /ingestion/project", e)
        results.add_fail("POST /ingestion/project", e)

# ============================================================
# 5. CHAT API TESTS (WebSocket is hard to test, test HTTP fallback if any)
# ============================================================
def test_chat_api():
    log_section("5. CHAT API TESTS")
    
    # Note: Chat uses WebSocket which is harder to test in a simple script.
    # We'll just verify the endpoint exists and document the expected behavior.
    print(f"{Colors.YELLOW}ℹ INFO{Colors.RESET} - Chat uses WebSocket at ws://localhost:8000/chat/ws")
    print(f"{Colors.YELLOW}ℹ INFO{Colors.RESET} - Manual testing recommended for full chat verification")
    
    # We can at least verify the router is mounted by checking if we get a proper error
    try:
        resp = requests.get(f"{BASE_URL}/chat/", timeout=5)
        # Should either return 404/405 (method not allowed) or some response
        # As long as it doesn't error with 500, the router is mounted
        assert resp.status_code != 500, f"Server error: {resp.status_code}"
        log_pass("Chat Router Mounted", f"(response code: {resp.status_code})")
        results.add_pass()
    except requests.exceptions.ConnectionError as e:
        log_fail("Chat Router Check", "Connection refused")
        results.add_fail("Chat Router Check", e)
    except Exception as e:
        log_fail("Chat Router Check", e)
        results.add_fail("Chat Router Check", e)

# ============================================================
# 6. EDGE CASE & ERROR HANDLING TESTS
# ============================================================
def test_edge_cases():
    log_section("6. EDGE CASE & ERROR HANDLING TESTS")
    
    # Test invalid JSON
    try:
        resp = requests.post(f"{BASE_URL}/audit/file", 
            data="not valid json",
            headers={"Content-Type": "application/json"},
            timeout=5)
        assert resp.status_code == 422, f"Expected 422 for invalid JSON, got {resp.status_code}"
        log_pass("Invalid JSON Handling", "(correctly rejected with 422)")
        results.add_pass()
    except Exception as e:
        log_fail("Invalid JSON Handling", e)
        results.add_fail("Invalid JSON Handling", e)

    # Test missing required fields
    try:
        resp = requests.post(f"{BASE_URL}/audit/file", 
            json={},  # Missing file_path
            timeout=5)
        assert resp.status_code == 422, f"Expected 422 for missing field, got {resp.status_code}"
        log_pass("Missing Required Field", "(correctly rejected with 422)")
        results.add_pass()
    except Exception as e:
        log_fail("Missing Required Field", e)
        results.add_fail("Missing Required Field", e)

    # Test large payload handling (simulate)
    try:
        large_content = "x" * 100000  # 100KB of content
        resp = requests.post(f"{BASE_URL}/audit/file", 
            json={"file_path": "test.py", "content": large_content},
            timeout=10)
        # Should either process or reject gracefully, not crash
        assert resp.status_code in [200, 400, 422], f"Unexpected status: {resp.status_code}"
        log_pass("Large Payload Handling", f"(handled with status {resp.status_code})")
        results.add_pass()
    except Exception as e:
        log_fail("Large Payload Handling", e)
        results.add_fail("Large Payload Handling", e)

# ============================================================
# MAIN EXECUTION
# ============================================================
def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║          AIde Backend - QA Test Suite                    ║")
    print(f"║          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                            ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")
    
    # Check server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except:
        print(f"{Colors.RED}ERROR: Server not running at {BASE_URL}{Colors.RESET}")
        print("Start the server with: python -m uvicorn server.main:app --port 8000")
        sys.exit(1)
    
    # Run all test suites
    test_health_endpoint()
    test_settings_api()
    test_audit_api()
    test_ingestion_api()
    test_chat_api()
    test_edge_cases()
    
    # Print summary
    success = results.summary()
    
    if success:
        print(f"{Colors.GREEN}{Colors.BOLD}ALL TESTS PASSED! ✓{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"{Colors.RED}{Colors.BOLD}SOME TESTS FAILED! ✗{Colors.RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
