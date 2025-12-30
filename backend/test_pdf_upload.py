"""Comprehensive test for PDF upload and querying functionality"""
import requests
import sys
import os
import base64
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

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

def authenticate():
    """Authenticate and get token"""
    print_section("Authentication")
    username = "pdf_test_user2"
    password = "testpass123"
    
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
                return data["token"]
        elif response.status_code == 400:
            error = response.json().get("detail", "")
            if "already exists" in error.lower():
                print("[INFO] User exists, attempting login...")
            else:
                print(f"[WARNING] Signup failed: {error}")
        else:
            print(f"[WARNING] Signup failed with status {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Signup error: {e}")
    
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
                return data["token"]
        else:
            print(f"[ERROR] Login failed: {response.text}")
    except Exception as e:
        print(f"[ERROR] Login error: {e}")
    
    return None

def create_sample_pdf():
    """Create a sample PDF file for testing"""
    print_section("Creating Sample PDF")
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
        
        pdf_path = "sample_test_document.pdf"
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 100, "Sample Test Document")
        
        # Content
        c.setFont("Helvetica", 12)
        y_position = height - 150
        content = [
            "This is a test document for PDF upload functionality.",
            "",
            "Key Information:",
            "- Company Revenue: $1.5 billion in 2023",
            "- Growth Rate: 15% year-over-year",
            "- Market Share: 25% in the technology sector",
            "- Employee Count: 10,000 employees worldwide",
            "",
            "Financial Highlights:",
            "- Q1 2023: $350 million",
            "- Q2 2023: $380 million",
            "- Q3 2023: $400 million",
            "- Q4 2023: $370 million",
            "",
            "The company has shown consistent growth over the past year.",
            "Key markets include North America, Europe, and Asia-Pacific."
        ]
        
        for line in content:
            c.drawString(100, y_position, line)
            y_position -= 20
            if y_position < 100:
                c.showPage()
                y_position = height - 100
        
        c.save()
        print(f"[OK] Sample PDF created: {pdf_path}")
        return pdf_path
    except ImportError:
        print("[WARNING] reportlab not installed. Creating a simple text-based PDF alternative...")
        # Create a simple text file that can be used for testing
        # (In real scenario, user would provide their own PDF)
        print("[INFO] Please provide a PDF file manually for testing.")
        print("[INFO] Expected file: sample_test_document.pdf")
        return None
    except Exception as e:
        print(f"[ERROR] Error creating PDF: {e}")
        return None

def upload_pdf(token, pdf_path):
    """Upload PDF file"""
    print_section("Uploading PDF")
    
    if not pdf_path or not os.path.exists(pdf_path):
        print("[ERROR] PDF file not found. Please provide a valid PDF file.")
        return False
    
    try:
        print(f"Uploading: {pdf_path}")
        with open(pdf_path, "rb") as f:
            files = {"file": (os.path.basename(pdf_path), f, "application/pdf")}
            headers = {"token": token}
            response = requests.post(
                f"{BASE_URL}/upload-pdf",
                files=files,
                headers=headers,
                timeout=600  # 10 minutes for PDF processing (first time may download OCR models)
            )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("[OK] PDF uploaded successfully!")
            print(f"   Filename: {data.get('filename', 'N/A')}")
            print(f"   Chunks stored: {data.get('chunks_stored', 'N/A')}")
            return True
        else:
            print(f"[ERROR] Upload failed: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Upload error: {e}")
        return False

def query_pdf(token, query, thread_id):
    """Query about the uploaded PDF"""
    print_section("Querying PDF Content")
    print(f"Query: {query}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": query,
                "thread_id": thread_id
            },
            headers={"token": token},
            timeout=300  # 5 minutes for complex queries
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            # Handle case where answer might be a list
            if isinstance(answer, list):
                answer = " ".join(str(item) for item in answer)
            elif not isinstance(answer, str):
                answer = str(answer)
            images = data.get("images", [])
            
            print("[OK] Query successful!")
            print(f"\n{'-'*70}")
            print("RESPONSE:")
            print(f"{'-'*70}")
            print(answer[:500] + ("..." if len(answer) > 500 else ""))
            print(f"{'-'*70}")
            
            if images:
                print(f"\n[OK] {len(images)} image(s) generated!")
                for i, img in enumerate(images, 1):
                    filename = img.get("filename", f"image_{i}.png")
                    print(f"   Image {i}: {filename}")
                    
                    # Save the image
                    img_data = base64.b64decode(img.get("data", ""))
                    output_path = f"downloaded_{filename}"
                    with open(output_path, "wb") as f:
                        f.write(img_data)
                    print(f"   Saved to: {output_path}")
            else:
                print("\n[INFO] No images generated in this response")
            
            return True
        else:
            print(f"[ERROR] Query failed: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("[WARNING] Query timed out (this may be normal for complex queries)")
        return False
    except Exception as e:
        print(f"[ERROR] Query error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_visualization(token, thread_id):
    """Test query that should generate a visualization"""
    print_section("Testing Visualization Generation")
    
    query = "If there is any numerical data or trends in the document, create a visualization or chart to represent it"
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": query,
                "thread_id": thread_id
            },
            headers={"token": token},
            timeout=300
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            images = data.get("images", [])
            
            print("[OK] Visualization query successful!")
            print(f"\nResponse preview: {answer[:200]}...")
            
            if images:
                print(f"\n[OK] {len(images)} visualization(s) generated!")
                for i, img in enumerate(images, 1):
                    filename = img.get("filename", f"image_{i}.png")
                    print(f"   Image {i}: {filename} ({len(img.get('data', ''))} bytes)")
                    
                    # Save the image
                    img_data = base64.b64decode(img.get("data", ""))
                    output_path = f"visualization_{filename}"
                    with open(output_path, "wb") as f:
                        f.write(img_data)
                    print(f"   Saved to: {output_path}")
                return True
            else:
                print("\n[WARNING] No images generated (query may not have required visualization)")
                return False
        else:
            print(f"[ERROR] Query failed: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def main():
    """Main test execution"""
    print("="*70)
    print("  PDF Upload and Query Test Suite")
    print("="*70)
    
    # Test 1: Server health
    if not test_server():
        print("\n[ERROR] Server health check failed. Please start the server first.")
        sys.exit(1)
    
    # Test 2: Authentication
    token = authenticate()
    if not token:
        print("\n[ERROR] Authentication failed")
        sys.exit(1)
    
    print(f"\n[OK] Token obtained: {token[:30]}...")
    
    # Test 3: Use provided PDF file
    pdf_path = 'AJP UNIT 1.1 (1).pdf'
    
    if pdf_path and not os.path.exists(pdf_path):
        print(f"\n[WARNING] PDF file '{pdf_path}' not found in current directory")
        print("[INFO] Please ensure the PDF file is in the same directory as this script")
        pdf_path = None
    
    # Test 4: Upload PDF
    if pdf_path:
        if not upload_pdf(token, pdf_path):
            print("\n[WARNING] PDF upload failed, but continuing with tests...")
    else:
        print("\n[INFO] Skipping PDF upload (no PDF file available)")
        print("[INFO] You can manually test PDF upload by providing a PDF file")
    
    # Test 5: Query about PDF content
    thread_id = f"pdf_test_thread_{int(time.time())}"
    
    queries = [
        "Summarize the main topics and key information from the document",
        "What are the important concepts discussed in the document?",
        "Explain the main content of the document in detail"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i}/{len(queries)} ---")
        query_pdf(token, query, thread_id)
        time.sleep(2)  # Small delay between queries
    
    # Test 6: Test visualization (if PDF was uploaded)
    if pdf_path:
        test_with_visualization(token, thread_id)
    
    # Cleanup
    if pdf_path and os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
            print(f"\n[INFO] Cleaned up sample PDF: {pdf_path}")
        except:
            pass
    
    print("\n" + "="*70)
    print("[OK] PDF Upload and Query Test Suite Completed!")
    print("="*70)

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

