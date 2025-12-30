import os
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv
import hashlib

load_dotenv()

class StrategicMemory:
    def __init__(self, google_api_key: str, pinecone_api_key: str, mongodb_uri: str):
        # 1. Initialize Google Embeddings (Dimension 768)
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=google_api_key
        )
        
        # 2. Initialize Pinecone
        self.pc = Pinecone(api_key=pinecone_api_key)
        index_name = os.getenv("PINECONE_INDEX_NAME", "research-index")
        self.index = self.pc.Index(index_name)
        
        # 3. Initialize MongoDB for conversation history
        self.mongo_client = AsyncIOMotorClient(mongodb_uri)
        self.db = self.mongo_client.agent_database

    def save_to_memory(self, query: str, report: str, user_id: str):
        """Saves the final report to the knowledge base with user isolation."""
        # Ensure metadata values are primitives (Pinecone requires str/number/bool or list[str])
        report_str = report if isinstance(report, str) else str(report)
        vector = self.embeddings.embed_query(query)
        
        # Create unique ID based on user_id and query hash
        query_hash = hashlib.md5(f"{user_id}_{query}".encode()).hexdigest()
        
        # Store in Pinecone with user_id in metadata for filtering
        self.index.upsert(
            vectors=[{
                "id": f"{user_id}_{query_hash}",
                "values": vector,
                "metadata": {
                    "report": report_str[:50000],  # Limit metadata size
                    "query": query[:1000],
                    "user_id": user_id
                }
            }],
            namespace=f"reports_{user_id}"  # User-specific namespace for reports
        )
        print("💾 Knowledge saved to Research Archive.")

    def query_memory(self, query: str, user_id: str, threshold: float = 0.85):
        """Checks if we already know the answer to this or something similar (user-specific)."""
        query_vector = self.embeddings.embed_query(query)
        results = self.index.query(
            vector=query_vector,
            top_k=1,
            include_metadata=True,
            namespace=f"reports_{user_id}",  # Query user-specific namespace
            filter={"user_id": user_id}  # Additional filtering
        )
        
        if results.get('matches') and results['matches'][0]['score'] >= threshold:
            return results['matches'][0]['metadata']['report']
        return None

    async def save_conversation(self, thread_id: str, user_id: str, messages: list):
        """Save conversation history to MongoDB."""
        try:
            await self.db.conversations.update_one(
                {"thread_id": thread_id, "user_id": user_id},
                {
                    "$set": {
                        "messages": messages,
                        "updated_at": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
        except Exception as e:
            print(f"Error saving conversation: {e}")

    async def load_conversation(self, thread_id: str, user_id: str):
        """Load conversation history from MongoDB."""
        try:
            doc = await self.db.conversations.find_one(
                {"thread_id": thread_id, "user_id": user_id}
            )
            if doc:
                return doc.get("messages", [])
            return []
        except Exception as e:
            print(f"Error loading conversation: {e}")
            return []