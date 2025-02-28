# Web Search API

A FastAPI-based web search API that uses the Brave Search API to perform searches and return web page contents.

## Features

- Search the web using Brave Search API
- Return the full content of web pages in search results
- Simple API for external AI agents

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
  "n": 3 // Number of pages to return (default: 3, max: 10)
}
```

**Headers**:

```
Authorization: Bearer your_brave_search_api_key_here
```

**Response**:

```json
{
  "results": [
    {
      "url": "https://example.com",
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

async def search_web(query: str, num_results: int = 3, api_key: str = None):
    url = "http://localhost:8000/search"
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {"q": query, "n": num_results}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
```

## API Key Configuration

You need a Brave Search API key to use this service. You can pass it in the Authorization header with each request.

## License

[MIT](LICENSE)
