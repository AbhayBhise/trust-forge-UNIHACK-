from ddgs import DDGS
import time
import logging

log = logging.getLogger(__name__)

class SearchAgent:
    """
    Programmatic Search Agent using DuckDuckGo Search API.
    Bypasses captchas entirely by calling the backend API directly via `ddgs`.
    """
    def __init__(self, max_results=3):
        self.max_results = max_results
        
    def find_urls(self, mpn: str, manufacturer: str = None) -> list[str]:
        """
        Find URLs for the MPN. Prioritize the manufacturer domain if provided.
        """
        urls = []
        try:
            with DDGS() as ddgs:
                # Build query
                query = f"{mpn} specifications"
                if manufacturer:
                    # Strip generic terms to get the core domain name
                    core_mfr = manufacturer.lower().replace("corporation", "").replace("manufacturing", "").strip()
                    query += f" site:{core_mfr}.com"
                
                log.info(f"SearchAgent: Querying DDG -> '{query}'")
                
                # Fetch results
                results = list(ddgs.text(query, max_results=self.max_results))
                
                for r in results:
                    href = r.get("href")
                    if href and href not in urls:
                        urls.append(href)
                        
                # Fallback if no results from site-specific search
                if not urls and manufacturer:
                    query = f"{mpn} specifications {manufacturer}"
                    log.info(f"SearchAgent: Fallback query -> '{query}'")
                    results = list(ddgs.text(query, max_results=self.max_results))
                    for r in results:
                        href = r.get("href")
                        if href and href not in urls:
                            urls.append(href)
                            
        except Exception as e:
            log.error(f"SearchAgent: Error querying DDG: {e}")
            
        return urls

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = SearchAgent()
    urls = agent.find_urls("PDSH4816AF", "Frigidaire")
    print("Found URLs:", urls)
