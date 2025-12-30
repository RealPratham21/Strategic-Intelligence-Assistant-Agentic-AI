# Strategic Intelligence Assistant

An advanced Agentic AI Research System with RAG (Retrieval-Augmented Generation) capabilities, PDF document processing, and intelligent research automation.

**Developed by: Prathamesh Bhamare**

## 🚀 Features

- **User Authentication**: Secure signup/login with JWT tokens
- **PDF Document Processing**: Upload PDFs for RAG-based question answering
- **Intelligent Research**: Automated web research with multiple tools
- **Data Visualization**: Automatic chart and graph generation
- **Conversation Memory**: Persistent conversation history via MongoDB
- **Semantic Search**: Pinecone vector database for document retrieval
- **Streamlit Dashboard**: Beautiful, user-friendly web interface

## 📁 Project Structure

```
Agentic AI Project/
├── backend/              # FastAPI backend server
│   ├── main.py          # FastAPI application and endpoints
│   ├── auth_service.py  # Authentication and user management
│   ├── graph_engine.py  # LangGraph workflow orchestration
│   ├── orchestrator.py  # LLM brain and tool coordination
│   ├── rag_engine.py    # RAG processing for PDFs
│   ├── memory_manager.py # Pinecone and MongoDB memory
│   ├── research_tools.py # Web search and scraping
│   ├── sandbox.py       # Python code execution sandbox
│   ├── pdf_tool.py      # PDF document reading tool
│   └── requirements.txt # Backend dependencies
├── frontend/            # Streamlit dashboard
│   ├── streamlit_app.py # Main dashboard application
│   └── requirements.txt # Frontend dependencies
├── .env                 # Environment variables (create this)
└── README.md           # This file
```

## 🛠️ Installation

### Prerequisites

- Python 3.11 or higher
- MongoDB Atlas account (or local MongoDB instance)
- Pinecone account
- Google Gemini API key

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd "Agentic AI Project"
```

### Step 2: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### Step 3: Install Frontend Dependencies

```bash
cd frontend
pip install -r requirements.txt
cd ..
```

### Step 4: Set Up Environment Variables

Create a `.env` file in the project root:

```env
# Google Gemini API Key
GOOGLE_API_KEY=your_google_api_key_here

# Pinecone API Key
PINECONE_API_KEY=your_pinecone_api_key_here

# MongoDB Connection String
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/agent_database?retryWrites=true&w=majority

# JWT Secret Key (generate a secure random string)
SECRET_KEY=your-secret-key-here

# Pinecone Index Name (optional, defaults to "research-index")
PINECONE_INDEX_NAME=research-index
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))"
```

### Step 5: Set Up Pinecone Index

1. Go to [Pinecone Console](https://www.pinecone.io/)
2. Create a new index:
   - **Name**: `research-index` (or match your `PINECONE_INDEX_NAME`)
   - **Dimensions**: `768` (for Google's text-embedding-004)
   - **Metric**: `cosine`

## 🚀 Running the Application

### Start the Backend Server

Open a terminal and run:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Start the Frontend Dashboard

Open another terminal and run:

```bash
cd frontend
streamlit run streamlit_app.py
```

The dashboard will open at `http://localhost:8501`

## 📖 Usage

### Using the Streamlit Dashboard

1. **Sign Up/Login**: Create an account or login with existing credentials
2. **Upload PDF** (Optional): Upload a PDF document for RAG-based queries
3. **Enter Query**: Type your question or research request
4. **Submit**: Click "Submit Query" to get results
5. **View Results**: See the answer and any generated visualizations

### Using the API Directly

#### 1. Sign Up
```bash
curl -X POST "http://localhost:8000/signup" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

#### 2. Login
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

#### 3. Upload PDF
```bash
curl -X POST "http://localhost:8000/upload-pdf" \
  -H "token: YOUR_TOKEN_HERE" \
  -F "file=@document.pdf"
```

#### 4. Send Query
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "token: YOUR_TOKEN_HERE" \
  -d '{
    "query": "Analyze revenue trends of tech companies",
    "thread_id": "thread_123"
  }'
```

## 🔧 System Architecture

### Components

1. **FastAPI Backend**: RESTful API with authentication
2. **LangGraph Workflow**: State machine for research orchestration
3. **RAG Engine**: PDF processing and semantic search
4. **Memory Manager**: Conversation history and knowledge base
5. **Research Tools**: Web search, scraping, and Python execution
6. **Streamlit Frontend**: User-friendly dashboard interface

### Workflow

1. User authenticates → Receives JWT token
2. User uploads PDF (optional) → Stored in Pinecone with user isolation
3. User sends query → System:
   - Checks cached responses
   - Retrieves relevant PDF context (if available)
   - Decides tools to use
   - Conducts research
   - Generates response and visualizations
   - Saves to memory
4. Response returned with text and images

## 🧪 Testing

### Run Backend Tests

```bash
cd backend
python test1.py          # Basic system test
python quick_test.py     # Quick health check
python test_pdf_upload.py # PDF upload and query test
```

## 📝 API Endpoints

- `POST /signup` - Create new user account
- `POST /login` - Authenticate and get token
- `POST /upload-pdf` - Upload PDF for RAG processing
- `POST /chat` - Send research query
- `GET /health` - Health check
- `GET /` - API information

## 🔐 Security

- Passwords are hashed using bcrypt
- JWT tokens for authentication
- User data isolation in Pinecone (namespaces)
- Input validation on all endpoints

## 🛠️ Technologies Used

- **FastAPI**: Modern Python web framework
- **Streamlit**: Interactive dashboard framework
- **LangChain**: LLM orchestration
- **LangGraph**: Workflow state management
- **Google Gemini**: LLM for reasoning
- **Pinecone**: Vector database for RAG
- **MongoDB**: Conversation history storage
- **Docling**: PDF document processing
- **Matplotlib**: Data visualization

## 📄 License

This project is developed by Prathamesh Bhamare.

## 🤝 Contributing

This is a personal project. For questions or suggestions, please contact the developer.

## 📧 Contact

**Developer**: Prathamesh Bhamare

---

**Note**: Make sure to keep your `.env` file secure and never commit it to version control.

