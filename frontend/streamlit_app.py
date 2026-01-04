"""Strategic Intelligence Assistant - Streamlit Dashboard"""
import streamlit as st
import requests
import base64
import os
from io import BytesIO
from PIL import Image

# BASE_URL = "https://strategic-intelligence-assistant-agentic.onrender.com"
BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Strategic Intelligence Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        color: #1f77b4;
    }
    .auth-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: #f0f2f6;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        border-radius: 5px;
        padding: 0.5rem;
        font-weight: bold;
    }
    .response-container {
        background: #f9f9f9;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

def check_server():
    """Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        return response.status_code == 200
    except:
        return False

def signup(username, password):
    """Sign up new user"""
    try:
        response = requests.post(
            f"{BASE_URL}/signup",
            json={"username": username, "password": password},
            timeout=120
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("token"), None
        else:
            error = response.json().get("detail", "Signup failed")
            return None, error
    except Exception as e:
        return None, str(e)

def login(username, password):
    """Login user"""
    try:
        response = requests.post(
            f"{BASE_URL}/login",
            json={"username": username, "password": password},
            timeout=120
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("token"), None
        else:
            error = response.json().get("detail", "Login failed")
            return None, error
    except Exception as e:
        return None, str(e)

def upload_pdf(token, file):
    """Upload PDF file"""
    try:
        files = {"file": (file.name, file.getvalue(), "application/pdf")}
        headers = {"token": token}
        response = requests.post(
            f"{BASE_URL}/upload-pdf",
            files=files,
            headers=headers,
            timeout=600  # 10 minutes for PDF processing
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            error = response.json().get("detail", "Upload failed")
            return None, error
    except Exception as e:
        return None, str(e)

def send_query(token, query, thread_id):
    """Send query to chat endpoint"""
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"query": query, "thread_id": thread_id},
            headers={"token": token},
            timeout=300  # 5 minutes
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            error = response.json().get("detail", "Query failed")
            return None, error
    except Exception as e:
        return None, str(e)

def main():
    # Initialize session state
    if "token" not in st.session_state:
        st.session_state.token = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"thread_{os.urandom(8).hex()}"
    
    # Check server connection
    if not check_server():
        st.error("⚠️ Server is not running! Please start the FastAPI server with: `uvicorn main:app --reload`")
        st.stop()
    
    # Authentication Page
    if not st.session_state.token:
        st.markdown('<h1 class="main-header">Strategic Intelligence Assistant</h1>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["Login", "Sign Up"])
            
            with tab1:
                st.markdown("### Login to Your Account")
                login_username = st.text_input("Username", key="login_user")
                login_password = st.text_input("Password", type="password", key="login_pass")
                
                if st.button("Login", key="login_btn"):
                    if login_username and login_password:
                        with st.spinner("Logging in..."):
                            token, error = login(login_username, login_password)
                            if token:
                                st.session_state.token = token
                                st.session_state.username = login_username
                                st.success("Login successful!")
                                st.rerun()
                            else:
                                st.error(f"Login failed: {error}")
                    else:
                        st.warning("Please enter both username and password")
            
            with tab2:
                st.markdown("### Create New Account")
                signup_username = st.text_input("Username", key="signup_user")
                signup_password = st.text_input("Password", type="password", key="signup_pass")
                signup_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
                
                if st.button("Sign Up", key="signup_btn"):
                    if signup_username and signup_password:
                        if signup_password == signup_confirm:
                            with st.spinner("Creating account..."):
                                token, error = signup(signup_username, signup_password)
                                if token:
                                    st.session_state.token = token
                                    st.session_state.username = signup_username
                                    st.success("Account created successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Signup failed: {error}")
                        else:
                            st.warning("Passwords do not match")
                    else:
                        st.warning("Please fill in all fields")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Main Dashboard
    else:
        # Sidebar for logout
        with st.sidebar:
            st.markdown(f"### Welcome, {st.session_state.username}!")
            if st.button("Logout"):
                st.session_state.token = None
                st.session_state.username = None
                st.rerun()
        
        # Main content
        st.markdown('<h1 class="main-header">🤖 Strategic Intelligence Assistant</h1>', unsafe_allow_html=True)
        
        # Credits
        st.markdown(
            '<div style="text-align: center; color: #666; margin-bottom: 1rem;">'
            'Developed by <strong>Prathamesh Bhamare</strong>'
            '</div>',
            unsafe_allow_html=True
        )
        
        # Create two columns for layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 📝 Enter Your Query")
            query = st.text_area(
                "Ask a question or request research:",
                height=150,
                placeholder="e.g., Analyze revenue trends of tech companies and create a visualization"
            )
            
            st.markdown("### 📄 Upload PDF (Optional)")
            uploaded_file = st.file_uploader(
                "Upload a PDF document for RAG-based queries",
                type=["pdf"],
                help="Upload a PDF to enable document-based question answering"
            )
            
            if uploaded_file is not None:
                if st.button("Upload PDF", key="upload_btn"):
                    with st.spinner("Uploading and processing PDF (this may take a few minutes)..."):
                        result, error = upload_pdf(st.session_state.token, uploaded_file)
                        if result:
                            st.success(f"✅ PDF uploaded successfully! ({result.get('chunks_stored', 0)} chunks stored)")
                        else:
                            st.error(f"Upload failed: {error}")
            
            submit_query = st.button("🚀 Submit Query", type="primary", use_container_width=True)
        
        with col2:
            st.markdown("### 💬 Response")
            
            if submit_query and query:
                with st.spinner("Processing your query (this may take a while)..."):
                    result, error = send_query(
                        st.session_state.token,
                        query,
                        st.session_state.thread_id
                    )
                    
                    if result:
                        answer = result.get("answer", "")
                        images = result.get("images", [])
                        
                        # Display answer
                        st.markdown('<div class="response-container">', unsafe_allow_html=True)
                        st.markdown("**Answer:**")
                        st.markdown(answer)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Display images if any
                        if images:
                            st.markdown("### 🖼️ Generated Visualizations")
                            for i, img_data in enumerate(images, 1):
                                try:
                                    # Decode base64 image
                                    img_bytes = base64.b64decode(img_data.get("data", ""))
                                    img = Image.open(BytesIO(img_bytes))
                                    
                                    st.markdown(f"**Image {i}:** {img_data.get('filename', f'image_{i}.png')}")
                                    st.image(img, use_container_width=True)
                                except Exception as e:
                                    st.warning(f"Could not display image {i}: {str(e)}")
                    else:
                        st.error(f"Query failed: {error}")
            elif submit_query:
                st.warning("Please enter a query first")
            else:
                st.info("👈 Enter a query and click 'Submit Query' to get started")

if __name__ == "__main__":
    main()

