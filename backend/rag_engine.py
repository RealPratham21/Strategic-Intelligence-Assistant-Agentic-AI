import os
from langchain_pinecone import PineconeVectorStore
from docling.document_converter import DocumentConverter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import uuid

load_dotenv()

class RAGEngine:
    def __init__(self, google_api_key: str):
        """Initialize RAG engine with embeddings."""
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=google_api_key
        )
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "research-index")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )

    async def process_pdf_for_user(self, file_path: str, user_id: str):
        """
        Process PDF file and store chunks in Pinecone with user isolation.
        Returns the number of chunks stored.
        """
        # 1. Parse with Docling
        converter = DocumentConverter()
        result = converter.convert(file_path)
        markdown_text = result.document.export_to_markdown()
        
        # 2. Split into chunks for better retrieval
        chunks = self.text_splitter.split_text(markdown_text)
        
        # 3. Store in Pinecone using the user_id as a Namespace
        vectorstore = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings,
            namespace=user_id  # ISOLATION KEY - each user has their own namespace
        )
        
        # Add chunks with metadata
        chunk_ids = [f"{user_id}_{uuid.uuid4()}" for _ in chunks]
        vectorstore.add_texts(
            texts=chunks,
            ids=chunk_ids,
            metadatas=[{"source": file_path, "user_id": user_id} for _ in chunks]
        )
        
        return len(chunks)

    async def retrieve_relevant_context(self, query: str, user_id: str, top_k: int = 5):
        """
        Retrieve relevant context from user's PDFs stored in Pinecone.
        Returns concatenated relevant chunks.
        """
        try:
            vectorstore = PineconeVectorStore(
                index_name=self.index_name,
                embedding=self.embeddings,
                namespace=user_id
            )
            
            # Perform similarity search
            results = await vectorstore.asimilarity_search(query, k=top_k)
            
            # Combine relevant chunks
            if results:
                context = "\n\n".join([doc.page_content for doc in results])
                return context if context.strip() else None
            return None
        except Exception as e:
            print(f"Error retrieving RAG context: {e}")
            return None

    async def check_user_has_documents(self, user_id: str) -> bool:
        """Check if user has any documents stored in their namespace."""
        try:
            vectorstore = PineconeVectorStore(
                index_name=self.index_name,
                embedding=self.embeddings,
                namespace=user_id
            )
            # Try to query with a dummy query to check if namespace has data
            results = await vectorstore.asimilarity_search("test", k=1)
            return len(results) > 0
        except Exception:
            return False