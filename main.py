import os
from enum import Enum
from typing import Annotated, List, Dict, Optional
import asyncio

from fastapi import FastAPI, Query, HTTPException, Header, Depends
from pydantic import BaseModel, Field
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")

app = FastAPI(
    title="Web Search API",
    description="API for searching web pages using Brave Search API",
    version="0.1.0",
)

# Request and response models
class SearchRequest(BaseModel):
    q: str = Field(description="Search query")
    n: int = Field(5, description="Number of pages to return", ge=1, le=15)

class PageResult(BaseModel):
    url: str = Field(..., description="URL of the page")
    page_contents: str = Field(..., description="Contents of the page")

class SearchResponse(BaseModel):
    results: List[PageResult] = Field(..., description="List of search results")

# API endpoints
@app.post("/search", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    authorization: Annotated[str | None, Header()]
):
    if authorization and authorization.startswith("Bearer "):
        brave_api_key = authorization.replace("Bearer ", "")
    
    brave_api_key = BRAVE_SEARCH_API_KEY
    if authorization and authorization.startswith("Bearer "):
        brave_api_key = authorization.replace("Bearer ", "")
    if not brave_api_key:
        raise HTTPException(
            status_code=403,
            detail="Brave Search API key is needed to use this service!"
        )

    # Make request to Brave Search API
    async with httpx.AsyncClient() as client:
        try:
            brave_search_url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": brave_api_key
            }
            params = {
                "q": body.q,
                "count": body.n  # This might need adjustment based on Brave's API
            }
            
            search_response = await client.get(brave_search_url, headers=headers, params=params)
            search_response.raise_for_status()
            search_results = search_response.json()
            
            # Extract URLs from search results
            # Note: The exact structure might need to be adjusted based on Brave's API response
            urls = []
            if "web" in search_results and "results" in search_results["web"]:
                urls = [result["url"] for result in search_results["web"]["results"][:body.n]]
            
            if not urls:
                return SearchResponse(results=[])
            
            # Define a helper function to fetch a single URL
            async def fetch_url_content(url: str, client: httpx.AsyncClient) -> Optional[PageResult]:
                try:
                    page_response = await client.get(url, timeout=5.0, follow_redirects=True)
                    page_response.raise_for_status()
                    
                    # Parse HTML and extract text content
                    soup = BeautifulSoup(page_response.text, "html.parser")
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.extract()
                    
                    # Get text content
                    text = soup.get_text(separator="\n", strip=True)
                    
                    return PageResult(url=url, page_contents=text)
                except Exception as e:
                    # If we can't fetch a page, we'll return None
                    return None
            
            # Fetch all URLs in parallel
            tasks = [fetch_url_content(url, client) for url in urls]
            results_with_none = await asyncio.gather(*tasks)
            
            # Filter out None results (failed fetches)
            results = [result for result in results_with_none if result is not None]
            
            return SearchResponse(results=results)
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error from Brave Search API: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error during search: {str(e)}")