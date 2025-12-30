"""Quick test to verify the system works"""
import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test server health"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("[OK] Server is healthy")
            return True
        else:
            print(f"[ERROR] Server returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] Server is not running! Start it with: uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def test_signup():
    """Test user signup"""
    print("\nTesting signup...")
    try:
        response = requests.post(
            f"{BASE_URL}/signup",
            json={"username": "testuser3", "password": "testpass123"},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                print("[OK] Signup successful")
                return data["token"]
            else:
                print("[WARNING] No token in response")
        elif response.status_code == 400:
            error = response.json().get("detail", "Unknown error")
            print(f"[INFO] Signup failed (may be expected if user exists): {error}")
            # Try login instead
            return test_login()
        else:
            print(f"[ERROR] Signup failed: {response.text}")
    except Exception as e:
        print(f"[ERROR] {e}")
    return None

def test_login():
    """Test user login"""
    print("\nTesting login...")
    try:
        response = requests.post(
            f"{BASE_URL}/login",
            json={"username": "testuser3", "password": "testpass123"},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                print("[OK] Login successful")
                return data["token"]
        else:
            print(f"[ERROR] Login failed: {response.text}")
    except Exception as e:
        print(f"[ERROR] {e}")
    return None

def test_chat(token):
    """Test chat endpoint"""
    print("\nTesting chat endpoint...")
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "What is 2+2?",
                "thread_id": "test_thread_quick"
            },
            headers={"token": token},
            timeout=60
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            print(f"[OK] Chat successful")
            print(f"Response preview: {answer[:100]}...")
            return True
        else:
            print(f"[ERROR] Chat failed: {response.text}")
    except requests.exceptions.Timeout:
        print("[WARNING] Chat request timed out (this may be normal for complex queries)")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
    return False

if __name__ == "__main__":
    print("="*60)
    print("Quick System Test")
    print("="*60)
    
    # Test 1: Health check
    if not test_health():
        print("\n[ERROR] Server health check failed. Please start the server first.")
        sys.exit(1)
    
    # Test 2: Authentication
    token = test_signup()
    if not token:
        print("\n[ERROR] Authentication failed")
        sys.exit(1)
    
    print(f"\n[OK] Token obtained: {token[:30]}...")
    
    # Test 3: Chat (optional - may take time)
    print("\n" + "="*60)
    print("Testing chat endpoint (this may take a while)...")
    print("="*60)
    test_chat(token)
    
    print("\n" + "="*60)
    print("[OK] Basic system tests completed!")
    print("="*60)

