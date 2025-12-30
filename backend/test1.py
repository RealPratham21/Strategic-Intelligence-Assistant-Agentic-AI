import requests
import sys
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_server():
    """Test if server is running"""
    print_section("Testing Server Connection")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("[OK] Server is running and healthy")
            return True
        else:
            print(f"[ERROR] Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] Server is not running!")
        print("   Please start the server with: uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"[ERROR] Error connecting to server: {e}")
        return False

def signup_or_login(username, password):
    """Try to signup, if user exists, try login"""
    print_section("Authentication")
    
    # Try signup first
    print(f"Attempting to sign up as '{username}'...")
    try:
        response = requests.post(
            f"{BASE_URL}/signup",
            json={"username": username, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                print("[OK] Signup successful!")
                print(f"   User ID: {data.get('user_id', 'N/A')}")
                return data["token"]
            else:
                print("[WARNING] Signup response missing token")
                print(f"   Response: {data}")
        elif response.status_code == 400:
            error_data = response.json()
            error_msg = error_data.get("detail", "Unknown error")
            print(f"[WARNING] Signup failed: {error_msg}")
            
            # If username exists, try login
            if "already exists" in error_msg.lower():
                print(f"   User exists, attempting login...")
            else:
                return None
        else:
            print(f"[ERROR] Signup failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', error_data)}")
            except:
                print(f"   Error: {response.text}")
            return None
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out")
        return None
    except Exception as e:
        print(f"[ERROR] Error during signup: {e}")
        return None
    
    # Try login
    print(f"Attempting to login as '{username}'...")
    try:
        response = requests.post(
            f"{BASE_URL}/login",
            json={"username": username, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                print("[OK] Login successful!")
                print(f"   User ID: {data.get('user_id', 'N/A')}")
                return data["token"]
            else:
                print("[WARNING] Login response missing token")
        elif response.status_code == 401:
            print("[ERROR] Invalid credentials")
        else:
            print(f"[ERROR] Login failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', error_data)}")
            except:
                print(f"   Error: {response.text}")
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out")
    except Exception as e:
        print(f"[ERROR] Error during login: {e}")
    
    return None

def send_chat_query(token, query, thread_id):
    """Send a chat query"""
    print_section("Sending Chat Query")
    print(f"Query: {query}")
    print(f"Thread ID: {thread_id}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"query": query, "thread_id": thread_id},
            headers={"token": token},
            timeout=300  # 5 minutes for research queries
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "No answer in response")
            print("[OK] Query successful!")
            print(f"\n{'-'*60}")
            print("RESPONSE:")
            print(f"{'-'*60}")
            print(answer[:500] + ("..." if len(answer) > 500 else ""))
            print(f"{'-'*60}")
            return result
        else:
            print(f"[ERROR] Query failed!")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', error_data)}")
            except:
                print(f"   Error: {response.text}")
            return None
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out (query took too long)")
        return None
    except Exception as e:
        print(f"[ERROR] Error sending query: {e}")
        return None

def main():
    """Main execution flow"""
    print_section("Agentic AI Research System - Test Script")
    
    # Test server
    if not test_server():
        sys.exit(1)
    
    # Authentication
    username = "testuser2"
    password = "testpass123"
    token = signup_or_login(username, password)
    
    if not token:
        print("\n[ERROR] Authentication failed. Cannot proceed.")
        sys.exit(1)
    
    print(f"\n[OK] Token obtained: {token[:50]}...")
    
    # Send query
    query = "Analyze revenue trends of tech companies and visualize it in a line graph"
    thread_id = "my_thread_1"
    
    result = send_chat_query(token, query, thread_id)
    
    if result:
        print("\n[OK] Test completed successfully!")
    else:
        print("\n[WARNING] Test completed with errors")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
