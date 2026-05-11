#!/usr/bin/env python3
"""Full API Test for QQPet Backend (Actual API Paths)"""

import http.client
import json
from typing import Dict, Optional

BASE_URL = "localhost:8000"

class APIClient:
    def __init__(self):
        self.conn = http.client.HTTPConnection(BASE_URL)
        self.token: Optional[str] = None
    
    def request(self, method: str, path: str, data: Optional[Dict] = None, auth: bool = True) -> Dict:
        headers = {"Content-Type": "application/json"}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        body = json.dumps(data) if data else None
        self.conn.request(method, path, body, headers)
        response = self.conn.getresponse()
        result = json.loads(response.read().decode())
        return result

def test_health():
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    client = APIClient()
    result = client.request("GET", "/health", auth=False)
    print(f"Response: {result}")
    assert result.get("status") == "healthy", "Health check failed"
    print("PASSED")

def test_register_login():
    print("\n" + "="*60)
    print("TEST 2: Auth - Register & Login")
    print("="*60)
    client = APIClient()
    
    print("\n--- Register new user ---")
    register_data = {"username": "testuser_docker", "password": "testpass123"}
    result = client.request("POST", "/api/auth/register", register_data, auth=False)
    print(f"Register Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    assert result.get("username") == "testuser_docker", "Register failed"
    
    print("\n--- Login ---")
    login_data = {"username": "testuser_docker", "password": "testpass123"}
    result = client.request("POST", "/api/auth/login", login_data, auth=False)
    print(f"Login Response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
    
    assert "access_token" in result, "Login failed - no access_token"
    client.token = result["access_token"]
    print("PASSED")
    return client

def test_user_info(client: APIClient):
    print("\n" + "="*60)
    print("TEST 3: User Info")
    print("="*60)
    
    print("\n--- Get Current User ---")
    result = client.request("GET", "/api/auth/me")
    print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    assert result.get("username") == "testuser_docker", "User info mismatch"
    print("PASSED")

def test_pet(client: APIClient):
    print("\n" + "="*60)
    print("TEST 4: Pet Data")
    print("="*60)
    
    print("\n--- Get Pet (auto-creates if not exists) ---")
    result = client.request("GET", "/api/pet")
    print(f"Get Response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
    assert "info" in result, "Get pet failed"
    
    print("\n--- Update Pet (PATCH) ---")
    update_data = {"info": {"name": "DockerPet", "hunger": 2000}}
    result = client.request("PATCH", "/api/pet", update_data)
    print(f"Update Response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
    assert result["info"]["name"] == "DockerPet", "Update pet failed"
    
    print("\n--- Get Pet Info ---")
    result = client.request("GET", "/api/pet/info")
    print(f"Info Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    print("PASSED")

def test_inventory(client: APIClient):
    print("\n" + "="*60)
    print("TEST 5: Inventory")
    print("="*60)
    
    print("\n--- Get Inventory ---")
    result = client.request("GET", "/api/pet/inventory")
    print(f"Get Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    assert "food" in result, "Get inventory failed"
    
    print("\n--- Update Inventory (PATCH) ---")
    update_data = {"food": ["_test_item-5"]}
    result = client.request("PATCH", "/api/pet/inventory", update_data)
    print(f"Update Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    assert "_test_item-5" in result["food"], "Update inventory failed"
    
    print("PASSED")

def test_settings(client: APIClient):
    print("\n" + "="*60)
    print("TEST 6: Settings")
    print("="*60)
    
    print("\n--- Get Settings ---")
    result = client.request("GET", "/api/pet/settings")
    print(f"Get Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    assert "stop_growth" in result, "Get settings failed"
    
    print("\n--- Update Settings (PATCH) ---")
    update_data = {"stop_growth": True, "shortcuts": {"test": "value"}}
    result = client.request("PATCH", "/api/pet/settings", update_data)
    print(f"Update Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    assert result["stop_growth"] == True, "Update settings failed"
    
    print("PASSED")

def test_logout(client: APIClient):
    print("\n" + "="*60)
    print("TEST 7: Logout")
    print("="*60)
    
    result = client.request("POST", "/api/auth/logout")
    print(f"Logout Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    print("PASSED")

def main():
    print("="*60)
    print("QQPET BACKEND FULL API TEST (DOCKER)")
    print("="*60)
    
    test_health()
    client = test_register_login()
    test_user_info(client)
    test_pet(client)
    test_inventory(client)
    test_settings(client)
    test_logout(client)
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! (7/7 Endpoints)")
    print("="*60)

if __name__ == "__main__":
    main()
