import os
import time
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from research_tools import ResearchToolkit
from sandbox import LogicSandbox
from pdf_tool import read_pdf_document
from dotenv import load_dotenv
from langchain_core.rate_limiters import InMemoryRateLimiter

load_dotenv()

# --- WRAPPING TOOLS ---

@tool
def web_search(query: str):
    """
    Search the web for real-time information, news, or specific facts.
    Use this for any query that requires up-to-date data.
    """
    return ResearchToolkit.search_web(query)

@tool
async def scrape_site(url: str):
    """
    Scrape and read the full content of a specific webpage. 
    Use this after getting a URL from a search to understand the details.
    """
    return await ResearchToolkit.scrape_url(url)

@tool
def execute_python(code: str, output_filename: str | None = "output_chart.png"):
    """
    Run Python for calculations, data analysis, or visual plotting.
    - `code`: The Python script to execute.
    - `output_filename`: Filename to save any generated plots.
    The environment includes 'plt' (matplotlib), 'pd' (pandas), and 'np' (numpy).
    ALWAYS call plt.savefig(output_filename) if you generate a chart.
    """
    sandbox = LogicSandbox()
    return sandbox.run_code(code, output_filename=output_filename)

# --- THE BRAIN ---

rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.06,  # 1 request / 15 seconds
    check_every_n_seconds=0.1,
    max_bucket_size=1
)

class StrategicBrain:
    def __init__(self, api_key: str):
        # Gemini 2.5 Flash-Lite: Optimized for high-frequency tool calling and long context.
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite", 
            google_api_key=api_key,
            temperature=0,
            max_output_tokens=4096,
            rate_limiter=rate_limiter,
            max_retries=6,
            timeout=60 
        )
        
        # Distiller: A separate instance for context compression to save RPD/TPM
        self.distiller = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=api_key,
            temperature=0,
            max_output_tokens=4096,
        )
        
        # Binding all dynamic tools
        self.tools = [web_search, scrape_site, execute_python, read_pdf_document]
        self.model_with_tools = self.llm.bind_tools(self.tools)

    def get_response(self, messages):
        """
        Orchestrates the next step in the reasoning chain.
        Implements context pruning to stay within Free Tier TPM limits.
        """
        # Maintain history: System + First User Prompt + last 3 tool turns
        if len(messages) > 5:
            pruned = [messages[0]] + messages[-4:]
        else:
            pruned = messages

        instruction = SystemMessage(content=(
            "You are a Strategic Researcher. Your objective is to solve complex queries "
            "autonomously using the available tools.\n\n"
            "GUIDELINES:\n"
            "1. DISCOVERY: Use 'web_search' for current facts. If a URL is found, 'scrape_site' to read it.\n"
            "2. LOCAL INTEL: Use 'read_pdf_document' if the user provides a file path or document reference.\n"
            "3. PDF CONTEXT: If you see '[FROM YOUR DOCUMENTS]' in the context, that means relevant information "
            "from the user's uploaded PDFs has been retrieved. PRIORITIZE this information and use it to answer the query. "
            "Do NOT search the web if the answer is in the documents.\n"
            "4. ANALYSIS: Use 'execute_python' to calculate growth rates, statistics, or generate charts.\n"
            "5. VISUALIZATION: When asked for a chart, write valid matplotlib code and "
            "ALWAYS include plt.savefig('output_chart.png').\n"
            "6. CONTEXT AWARENESS: You have access to a long-term memory (Pinecone). "
            "If the information is retrieved from memory, summarize it immediately.\n"
            "7. TERMINATION: Once the information is gathered, provide a comprehensive textual report. "
            "Do not call tools if the answer is already in the context history."
        ))
        
        # RPM mitigation for Free Tier
        time.sleep(2) 
        return self.model_with_tools.invoke([instruction] + pruned)

    def distill_scrape(self, raw_text: str, query: str) -> str:
        """
        Compresses large document/web data into high-density insights.
        """
        truncated_text = raw_text[:15000] # Fit within standard token limits
        prompt = f"Topic: {query}. Extract specific metrics, dates, and core facts from this raw text:\n\n{truncated_text}"
        
        try:
            response = self.distiller.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Context distillation failed: {str(e)[:100]}"

# --- SANITY CHECK ---
if __name__ == "__main__":
    api_key = os.getenv("GOOGLE_API_KEY")
    brain = StrategicBrain(api_key=api_key)
    
    # Example of a complex, dynamic prompt
    test_prompt = "Find Alphabet's revenue for the last 5 years, calculate the CAGR using Python, and plot it."
    response = brain.get_response([HumanMessage(content=test_prompt)])
    
    print("🧠 Strategic Reasoning Phase 1:")
    for tool_call in response.tool_calls:
        print(f"-> Decision: Call {tool_call['name']} with {tool_call['args']}")