# Web Search API

A FastAPI-based web search API that uses the Brave Search API to perform searches and return web page contents.

## Features

- **Web Search Integration**: Leverages the Brave Search API to perform high-quality web searches
- **Content Extraction**: Automatically fetches and parses full webpage content from search results
- **HTML Cleaning**: Removes non-essential elements (meta, footer, nav, script, style, button, form tags and stylesheets) for cleaner content
- **Link Processing**: Preserves and formats links for better readability while maintaining reference information
- **Content Summarization**: Optional integration with Gemini AI model to provide focused, relevant content summaries
- **Direct URL Support**: Can directly fetch and process a specific URL instead of performing a search
- **Search Context**: Supports providing additional context for more targeted content extraction
- **Configurable Results**: Adjust the number of search results returned (1-15 pages)
- **Comprehensive API**: Simple RESTful API interface for integration with AI agents and other applications

## Installation

### Prerequisites

- Python 3.13+
- Brave Search API key

### Setup

1. Clone the repository
2. Install dependencies:

   ```
   pip install -e .
   ```

   or

   ```
   uv pip install -e .
   ```

3. Create a `.env` file in the root directory (optional):
   ```
   BRAVE_SEARCH_API_KEY=your_brave_search_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## Usage

### Starting the server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

### API Documentation

Once the server is running, you can access the OpenAPI documentation at:

- `http://localhost:8000/docs` - Swagger UI
- `http://localhost:8000/redoc` - ReDoc

### Search Endpoint

**Endpoint**: `POST /search`

**Request Body**:

```json
{
  "q": "your search query",
  "url": "https://example.com", // Optional: Direct URL to fetch instead of search
  "search_context": "Optional description of what to look for in the pages",
  "n": 3 // Number of pages to return (default: 3, min: 1, max: 15)
}
```

**Headers**:

```
x-brave-search-api-key: your_brave_search_api_key_here
```

**Response**:

```json
{
  "results": [
    {
      "url": "https://example.com",
      "page_title": "Example Title",
      "page_contents": "Content of the page..."
    }
    // More results...
  ]
}
```

## Integration with AI Agents

This API is designed to be called by external AI agents over HTTP. Here's an example of how to integrate it in Python:

```python
import httpx

async def search_web(query: str, search_context: str = "", num_results: int = 3, api_key: str = None, direct_url: str = None):
    url = "http://localhost:8000/search"
    headers = {"x-brave-search-api-key": api_key}
    data = {
        "q": query,
        "n": num_results,
        "search_context": search_context
    }

    if direct_url:
        data["url"] = direct_url

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
```

## API Key Configuration

You need a Brave Search API key to use this service. You can obtain one from the Brave Developer Portal and pass it in the `x-brave-search-api-key` header with each request.

Additionally, you can optionally configure a Gemini API key to enable content summarization:

```
BRAVE_SEARCH_API_KEY=your_brave_search_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

## License

[MIT](LICENSE)

> #VibeCoded (fml)
