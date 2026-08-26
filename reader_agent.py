import requests
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional
from base_agent import BaseAgent


class ReaderAgent(BaseAgent):
    """
    Reader agent that visits URLs, scrapes HTML, and extracts clean text.
    Attributes:
        headers: User-agent headers to mimic a browser
        timeout: Request timeout in seconds
    """
    
    def __init__(self, config: Optional[Dict[str, Any]]=None):
        """
        Initialize the reader agent.
        Args:
            config: Optional configuration for scraping limits and timeouts
        """
        super().__init__(
            name="ReaderAgent",
            description="Scrapes and extracts clean text from provided URLs",
            config=config or {}
        )
        self.timeout=self.config.get("timeout", 15)
        self.max_chars=self.config.get("max_chars_per_page", 5000)
        self.headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def validate_input(self, input_data: Dict[str, Any])-> bool:
        """
        Validate input data containing URLs.
        Args:
            input_data: Must contain 'urls' key as a list
        """
        if not isinstance(input_data, dict):
            return False
        
        urls = input_data.get("urls")
        if not urls or not isinstance(urls, list):
            return False
        
        return True

    def execute(self, input_data: Dict[str, Any])-> Dict[str, Any]:
        """
        Execute the scraping process for a list of URLs.
        Args:
            input_data: Dictionary containing:
                -urls (List[str]): List of URLs to scrape
                -max_pages (int, optional): Limit number of pages to process
        Returns:
            Dictionary containing scraped content and status
        """
        if not self.validate_input(input_data):
            return{
                "success": False,
                "error": "Invalid input. 'urls' key must be a non-empty list.",
                "data": None
            }
        urls= input_data.get("urls", [])
        max_pages= input_data.get("max_pages", 3) 
        
        scraped_contents= []
        errors= []

        for url in urls[:max_pages]:
            try:
                content = self._scrape_url(url)
                scraped_contents.append({
                    "url": url,
                    "content": content
                })
            except Exception as e:
                errors.append({"url": url, "error": str(e)})

        self.update_execution_time()

        return{
            "success": len(scraped_contents) > 0,
            "error": None if not errors else f"Failed to scrape {len(errors)} pages",
            "data": {
                "scraped_contents": scraped_contents,
                "errors": errors if errors else None,
                "pages_processed": len(scraped_contents)
            }
        }

    def _scrape_url(self, url: str) -> str:
        """
        Perform the scraping and cleaning using BeautifulSoup.
        Args:
            url: The website link to process
        Returns:
            Cleaned text content
        """
        response= requests.get(
            url, 
            headers=self.headers, 
            timeout=self.timeout
        )
        response.raise_for_status()
        
        soup= BeautifulSoup(response.text, 'html.parser')
        
        for script_or_style in soup(["script", "style", "nav", "header", "footer"]):
            script_or_style.decompose()

        chunks= []
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
            text= element.get_text().strip()
            if text:
                chunks.append(text)

        full_text= " ".join(chunks)
        return full_text[:self.max_chars]
