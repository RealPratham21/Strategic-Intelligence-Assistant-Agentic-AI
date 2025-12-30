import os
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

# Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-ultra-secret-key-change-in-production")
ALGORITHM = "HS256"
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://...")

# Lazy MongoDB connection - only connect when needed
_client = None
_db = None

def get_db():
    """Get MongoDB database connection (lazy initialization)"""
    global _client, _db
    if _client is None:
        if not MONGODB_URI or MONGODB_URI == "mongodb+srv://...":
            raise ValueError("MONGODB_URI not properly configured in environment variables")
        _client = AsyncIOMotorClient(MONGODB_URI)
        _db = _client.agent_database
    return _db

class AuthService:
    @staticmethod
    async def create_user(username: str, password: str):
        """Create a new user account."""
        # Validate inputs
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")
        if not password:
            raise ValueError("Password cannot be empty")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        # Check password byte length (bcrypt limit is 72 bytes)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            raise ValueError("Password is too long (maximum 72 bytes)")
        
        # Get database connection
        db = get_db()
        
        # Check if user already exists
        existing = await db.users.find_one({"username": username.strip()})
        if existing:
            raise ValueError("Username already exists")
        
        # Hash password using bcrypt directly
        # This avoids passlib compatibility issues
        try:
            # Generate salt and hash password (password_bytes already encoded above)
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            # Store as string (bcrypt returns bytes)
            hashed_str = hashed.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Error hashing password: {str(e)}")
        
        result = await db.users.insert_one({
            "username": username.strip(), 
            "password": hashed_str,
            "created_at": datetime.utcnow()
        })
        return str(result.inserted_id)

    @staticmethod
    async def verify_user(username: str, password: str):
        """Verify user credentials and return user_id if valid."""
        if not username or not password:
            return None
        
        # Get database connection
        db = get_db()
        
        user = await db.users.find_one({"username": username.strip()})
        if not user:
            return None
        
        # Handle password verification using bcrypt directly
        try:
            # Encode password to bytes
            password_bytes = password.encode('utf-8')
            # Get stored hash (should be bytes or string)
            stored_hash = user["password"]
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')
            
            # Verify password
            if bcrypt.checkpw(password_bytes, stored_hash):
                return str(user["_id"])
        except Exception as e:
            print(f"Password verification error: {e}")
            return None
        return None

    @staticmethod
    def create_access_token(data: dict):
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str):
        """Decode and verify JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")