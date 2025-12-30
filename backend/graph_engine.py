import operator
import asyncio
import os
import glob
import re
from typing import Annotated, TypedDict, List, Literal

from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage, SystemMessage
from orchestrator import StrategicBrain
from memory_manager import StrategicMemory
from rag_engine import RAGEngine

import langchain

# 1. State Definition
class AgentState(TypedDict):
    # This keeps a chronological history of thoughts and tool observations
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str
    thread_id: str
    steps: int  # Track iteration count

class ResearchGraph:
    def __init__(self, api_key: str, pinecone_key: str, mongodb_uri: str):
        self.brain = StrategicBrain(api_key=api_key)
        self.memory = StrategicMemory(api_key, pinecone_key, mongodb_uri)
        self.rag_engine = RAGEngine(google_api_key=api_key)
        self.user_id = None
        self.thread_id = None
        
        workflow = StateGraph(AgentState)

        # --- NODES ---
        workflow.add_node("memory_check", self.check_cache)
        workflow.add_node("planner", self.call_model)
        workflow.add_node("executor", self.call_tool)

        # --- EDGES & ROUTING ---
        workflow.set_entry_point("memory_check")

        # Entry Logic: If Pinecone has a match, we bypass research entirely.
        workflow.add_conditional_edges(
            "memory_check",
            self.is_it_known,
            {"known": END, "unknown": "planner"}
        )

        # Reasoning Logic: Should we call a tool or finish the report?
        workflow.add_conditional_edges(
            "planner",
            self.should_continue,
            {"continue": "executor", "end": END}
        )
        
        # Action Loop: Always reflect on tool results before finishing.
        workflow.add_edge("executor", "planner")
        
        self.app = workflow.compile()

    # --- NODE LOGIC ---

    async def check_cache(self, state: AgentState):
        """Checks the Semantic Cache (Pinecone) for existing reports and RAG context."""
        query = state['messages'][0].content
        user_id = state.get('user_id', '')
        
        # 1. Check for cached reports
        cached_report = self.memory.query_memory(query, user_id)
        
        # 2. Check for relevant PDF context from RAG
        pdf_context = await self.rag_engine.retrieve_relevant_context(query, user_id)
        
        context_messages = []
        
        if cached_report:
            context_messages.append(AIMessage(content=f"🧠 [FROM MEMORY]\n{cached_report}"))
        
        if pdf_context and pdf_context.strip():
            context_messages.append(SystemMessage(
                content=f"📄 [FROM YOUR DOCUMENTS]\nRelevant context from your uploaded PDFs:\n\n{pdf_context}\n\nIMPORTANT: Use this information from the user's documents to answer their query. If the answer can be found in these documents, use it directly without searching the web."
            ))
        
        return {"messages": context_messages} 

    def is_it_known(self, state: AgentState) -> Literal["known", "unknown"]:
        """Reroutes based on whether cache hit occurred."""
        msgs = state.get('messages', [])
        if not msgs: return "unknown"
        last_msg = msgs[-1]
        if isinstance(last_msg, AIMessage) and "[FROM MEMORY]" in last_msg.content:
            return "known"
        return "unknown"

    def call_model(self, state: AgentState):
        current_steps = state.get("steps", 0)
        
        # If we are nearing our limit (e.g., step 8 of 10), 
        # we inject a 'Warning' into the system prompt.
        if current_steps > 8:
            state['messages'].append(SystemMessage(content=(
                "URGENT: You have only 2 steps left. STOP researching immediately. "
                "Use the information you already have to provide the best possible final answer."
            )))
        
        response = self.brain.get_response(state['messages'])
        return {"messages": [response], "steps": current_steps + 1}

    async def call_tool(self, state: AgentState):
        """Executes tools and handles context distillation for large inputs."""
        last_message = state['messages'][-1]
        tool_outputs = []
        original_query = state['messages'][0].content 
        user_id = state.get('user_id', '')

        for tool_call in last_message.tool_calls:
            tool_name = tool_call['name']
            args = tool_call['args']
            print(f"🛠️ Executing: {tool_name}")

            # DYNAMIC ROUTING
            if tool_name == "scrape_site":
                from orchestrator import scrape_site
                raw_result = await scrape_site.ainvoke(args)
                # EFFICIENCY: Compress large web data into small metrics
                result = self.brain.distill_scrape(str(raw_result), original_query)
            
            elif tool_name == "read_pdf_document":
                from orchestrator import read_pdf_document
                raw_result = read_pdf_document.invoke(args)
                # EFFICIENCY: Compress large PDF data
                result = self.brain.distill_scrape(str(raw_result), original_query)

            elif tool_name == "query_user_pdfs":
                # RAG retrieval tool for user's PDFs
                query_text = args.get('query', original_query)
                pdf_context = await self.rag_engine.retrieve_relevant_context(query_text, user_id)
                result = pdf_context if pdf_context else "No relevant information found in your uploaded documents."

            elif tool_name == "web_search":
                from orchestrator import web_search
                result = web_search.invoke(args)

            elif tool_name == "execute_python":
                from orchestrator import execute_python
                # Handles dynamic code + charting logic
                result = execute_python.invoke(args)

            tool_outputs.append(ToolMessage(content=str(result), tool_call_id=tool_call['id']))
        
        return {"messages": tool_outputs}

    def should_continue(self, state: AgentState):
        msgs = state.get('messages', [])
        last_message = msgs[-1]
        
        # Check if the LLM called a tool
        has_tool_calls = getattr(last_message, "tool_calls", None)
        
        # HARD CAP: If we've looped 12 times, force END even if it wants to search
        if state.get("steps", 0) >= 12:
            print("🛑 Hard budget reached. Forcing termination.")
            return "end"
            
        return "continue" if has_tool_calls else "end"

    async def run(self, query: str, thread_id: str, user_id: str):
        """
        Main entry point for running the research graph.
        Loads conversation history, runs the graph, and saves results.
        """
        self.user_id = user_id
        self.thread_id = thread_id
        
        # Load conversation history from MongoDB
        history = await self.memory.load_conversation(thread_id, user_id)
        
        # Convert history dicts back to LangChain messages
        messages = []
        if history:
            for msg in history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg.get("content", "")))
        
        # Add the new query
        messages.append(HumanMessage(content=query))
        
        # Initialize state
        initial_state = {
            "messages": messages,
            "user_id": user_id,
            "thread_id": thread_id,
            "steps": 0
        }
        
        config = {"recursion_limit": 20}
        final_msg = ""
        
        # Track existing PNG files before execution to only return newly created ones
        existing_files = set(glob.glob("*.png"))
        
        print("🚀 Starting Strategic Research...")
        async for output in self.app.astream(initial_state, config=config):
            for key, value in output.items():
                if not value:
                    continue
                print(f"Node: {key}")
                
                node_messages = value.get("messages", [])
                if not node_messages:
                    continue

                last_m = node_messages[-1]

                if key in ("planner", "memory_check"):
                    if not getattr(last_m, "tool_calls", None):
                        final_msg = last_m.content

        # Post-processing & archiving
        # Check for generated artifacts (Charts) - only return NEW files created during this run
        all_png_files = set(glob.glob("*.png"))
        generated_files = list(all_png_files - existing_files)
        
        if generated_files:
            print(f"📊 Visualizations generated: {generated_files}")
        
        if final_msg:
            # Save final report to Pinecone if this was fresh research
            if "[FROM MEMORY]" not in final_msg:
                self.memory.save_to_memory(query, final_msg, user_id)
            
            # Save conversation history to MongoDB
            # Convert all messages to dict format for storage
            all_messages = initial_state["messages"] + [AIMessage(content=final_msg)]
            messages_for_storage = []
            for m in all_messages:
                if isinstance(m, HumanMessage):
                    messages_for_storage.append({"role": "user", "content": m.content})
                elif isinstance(m, AIMessage):
                    messages_for_storage.append({"role": "assistant", "content": m.content})
                elif isinstance(m, SystemMessage):
                    messages_for_storage.append({"role": "system", "content": m.content})
            
            await self.memory.save_conversation(thread_id, user_id, messages_for_storage)
        
        # Return both message and generated files
        return {
            "answer": final_msg if final_msg else "I apologize, but I couldn't generate a response. Please try again.",
            "generated_files": generated_files
        }

# --- MAIN EXECUTION LOOP ---
if __name__ == "__main__":
    async def run_agent():
        # Credentials
        G_KEY = os.getenv("GOOGLE_API_KEY")
        P_KEY = os.getenv("PINECONE_API_KEY")
        MONGODB_URI = os.getenv("MONGODB_URI")
        
        researcher = ResearchGraph(api_key=G_KEY, pinecone_key=P_KEY, mongodb_uri=MONGODB_URI)
        
        # Dynamic Prompt
        query = "Analyze me Revenue of Mobile Companies like Apple, Samsung and other companies over the past few years. Also provide me a Line Graph for the same."
        thread_id = "test_thread_123"
        user_id = "test_user_123"
        
        result = await researcher.run(query, thread_id, user_id)
        print(f"\n✅ FINAL REPORT:\n{result}")

    asyncio.run(run_agent())