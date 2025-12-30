import asyncio
import json
from typing import List, Dict, Optional
from ddgs import DDGS
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

class ResearchToolkit:
    """
    Module 1: The Research Toolkit
    Provides Discovery (Search) and Extraction (Scraping) capabilities.
    """

    # Update your search_web function in research_tools.py
    @staticmethod
    def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query,
                    max_results=max_results,
                    safesearch="off"
                ))

            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                }
                for r in results
            ]

        except Exception as e:
            print(f"Search Tool Error: {e}")
            return []
    
    @staticmethod
    async def scrape_url(url: str) -> Optional[str]:
        """
        Deep-reads a URL and returns LLM-friendly Markdown.
        Uses Crawl4AI to handle dynamic JS content.
        """
        browser_config = BrowserConfig(headless=True)
        run_config = CrawlerRunConfig(
            word_count_threshold=20,  # Exclude short text like 'Buy Now'
            remove_overlay_elements=True,
            process_iframes=True
        )

        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=url, config=run_config)
                if result.success:
                    # Return the markdown representation of the page
                    return result.markdown
                else:
                    print(f"Scrape Error for {url}: {result.error_message}")
                    return None
        except Exception as e:
            print(f"Scraper Runtime Error: {e}")
            return None

# --- SANITY CHECK SCRIPT ---
if __name__ == "__main__":
    async def run_test():
        toolkit = ResearchToolkit()
        
        print("🔍 Testing Search...")
        links = ResearchToolkit.search_web(
            "Why did Indigo Airlines India receive backlash for its customer service in 2025?",
            max_results=3
        )

        print(links)

        print(f"Found {len(links)} results.")
        
        if links:
            print(f"📖 Testing Scraper on: {links[0]['url']}...")
            content = await toolkit.scrape_url(links[0]['url'])
            if content:
                print("✅ Success! First 300 chars of research data:")
                print(content[:300])
            else:
                print("❌ Scrape failed.")

    asyncio.run(run_test())