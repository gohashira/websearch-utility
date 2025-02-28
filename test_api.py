import asyncio
import os
import httpx
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_search_api():
    """Test the search API with a sample query."""
    # Get API key from environment variable or use a default for testing
    api_key = os.getenv("BRAVE_SEARCH_API_KEY", "your_api_key_here")
    
    # API endpoint
    url = "http://localhost:8000/search"
    
    # Request data
    data = {
        "q": "latest AI developments",
        "n": 2  # Limit to 2 results for testing
    }
    
    # Headers with authorization
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"Making request to {url} with query: {data['q']}")
    
    # Make the request
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            # Parse and display results
            results = response.json()
            
            print("\nSearch Results:")
            print("==============")
            
            for i, result in enumerate(results.get("results", [])):
                print(f"\nResult {i+1}")
                print(f"URL: {result.get('url')}")
                
                # Truncate page contents for display
                content = result.get("page_contents", "")
                truncated_content = content[:500] + "..." if len(content) > 500 else content
                print(f"Content (truncated): {truncated_content}")
                
            print(f"\nTotal results: {len(results.get('results', []))}")
            
        except httpx.HTTPStatusError as e:
            print(f"Error: HTTP {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_search_api()) 