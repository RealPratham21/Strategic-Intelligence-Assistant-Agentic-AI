import os
import base64
from fastapi import FastAPI, Depends, Header, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from auth_service import AuthService
from graph_engine import ResearchGraph
from rag_engine import RAGEngine
import uuid
import tempfile

load_dotenv()

app = FastAPI(title="Strategic Intelligence Assistant API")

# Configure CORS to allow requests from any domain
# For production, you can set ALLOWED_ORIGINS in .env to specify allowed domains
# Example: ALLOWED_ORIGINS=http://localhost:8501,https://yourdomain.com
# If not set, allows all origins (useful for development and deployment)
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
    allow_credentials = True
else:
    allowed_origins = ["*"]  # Allow all origins
    allow_credentials = False  # Cannot use credentials with wildcard

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers (including Authorization, token, etc.)
)

# Initialize services
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")

# Request models
class SignupRequest(BaseModel):
    username: str
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "testuser",
                "password": "testpass123"
            }
        }

class LoginRequest(BaseModel):
    username: str
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "testuser",
                "password": "testpass123"
            }
        }

class ChatRequest(BaseModel):
    query: str
    thread_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the revenue of Apple in 2023?",
                "thread_id": "thread_123"
            }
        }

# --- AUTHENTICATION ENDPOINTS ---

@app.post("/signup")
async def signup(request: SignupRequest):
    """Create a new user account."""
    try:
        # Validate MongoDB connection
        if not MONGODB_URI or MONGODB_URI == "mongodb+srv://...":
            raise HTTPException(status_code=500, detail="MONGODB_URI not properly configured")
        
        user_id = await AuthService.create_user(request.username, request.password)
        token = AuthService.create_access_token({"user_id": user_id, "username": request.username})
        return {
            "message": "User created successfully",
            "token": token,
            "user_id": user_id,
            "status": "success"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        print(f"Signup error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@app.post("/login")
async def login(request: LoginRequest):
    """Login and get access token."""
    try:
        # Validate MongoDB connection
        if not MONGODB_URI or MONGODB_URI == "mongodb+srv://...":
            raise HTTPException(status_code=500, detail="MONGODB_URI not properly configured")
        
        user_id = await AuthService.verify_user(request.username, request.password)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        token = AuthService.create_access_token({"user_id": user_id, "username": request.username})
        return {
            "message": "Login successful",
            "token": token,
            "user_id": user_id,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Login error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")

# --- PDF UPLOAD ENDPOINT ---

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), token: str = Header(...)):
    """Upload a PDF file for RAG processing."""
    try:
        # Verify user
        user_data = AuthService.decode_token(token)
        user_id = user_data["user_id"]
        
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Process PDF and store in Pinecone
            print(f"Processing PDF for user {user_id}...")
            rag_engine = RAGEngine(google_api_key=GOOGLE_API_KEY)
            chunks_count = await rag_engine.process_pdf_for_user(tmp_file_path, user_id)
            
            print(f"PDF processed successfully: {chunks_count} chunks stored")
            return {
                "message": "PDF processed and stored successfully",
                "filename": file.filename,
                "chunks_stored": chunks_count,
                "status": "success"
            }
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

# --- CHAT ENDPOINT ---

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, token: str = Header(...)):
    """Main chat endpoint for research queries."""
    try:
        # Validate inputs
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        if not request.thread_id or not request.thread_id.strip():
            raise HTTPException(status_code=400, detail="Thread ID cannot be empty")
        
        # Check if API keys are configured
        if not GOOGLE_API_KEY:
            raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured")
        if not PINECONE_API_KEY:
            raise HTTPException(status_code=500, detail="PINECONE_API_KEY not configured")
        if not MONGODB_URI:
            raise HTTPException(status_code=500, detail="MONGODB_URI not configured")
        
        # 1. Verify User via JWT
        try:
            user_data = AuthService.decode_token(token)
            user_id = user_data["user_id"]
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
        
        # 2. Initialize Research Graph with all required credentials
        try:
            system = ResearchGraph(
                api_key=GOOGLE_API_KEY,
                pinecone_key=PINECONE_API_KEY,
                mongodb_uri=MONGODB_URI
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize research system: {str(e)}")
        
        # 3. Run the Graph (It will automatically load history from MongoDB based on thread_id)
        try:
            result = await system.run(request.query.strip(), request.thread_id.strip(), user_id)
            
            # Handle both old format (string) and new format (dict)
            if isinstance(result, dict):
                answer = result.get("answer", "I apologize, but I couldn't generate a response. Please try again.")
                generated_files = result.get("generated_files", [])
            else:
                # Backward compatibility with old string response
                answer = result if result else "I apologize, but I couldn't generate a response. Please try again."
                generated_files = []
            
            # Ensure answer is a string
            if isinstance(answer, list):
                answer = " ".join(str(item) for item in answer)
            elif not isinstance(answer, str):
                answer = str(answer)
            
            # Convert image files to base64 for API response (only newly created files)
            image_data = []
            for img_file in generated_files:
                if os.path.exists(img_file):
                    try:
                        with open(img_file, "rb") as f:
                            img_base64 = base64.b64encode(f.read()).decode('utf-8')
                            image_data.append({
                                "filename": os.path.basename(img_file),
                                "data": img_base64,
                                "type": "image/png"
                            })
                    except Exception as e:
                        print(f"Error encoding image {img_file}: {e}")
            
            response_data = {"answer": answer}
            if image_data:
                response_data["images"] = image_data
            
            return response_data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# --- HEALTH CHECK ---

@app.get("/")
async def root():
    return {"message": "Strategic Intelligence Assistant API", "status": "running"}

@app.get("/health")
async def health():
    """Health check endpoint for deployment monitoring"""
    try:
        # Basic health check - don't connect to databases here to avoid blocking
        return {"status": "healthy", "service": "Strategic Intelligence Assistant API"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}