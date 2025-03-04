import asyncio
import os
import re
from typing import Annotated, List, Optional

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

load_dotenv()

BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    api_key=GEMINI_API_KEY,
)


def get_prompt(text: str, query: str):
    return f"""
        You are a machine that takes in text of a webpage and
        if the search query is relevant to the page,
            returns a comprehensive yet focussed version of the page containing all the relevant information.
        if the search query is not relevant to the page,
            returns "NOT RELEVANT" and nothing else.

        YOU MUST NOT ADD YOUR OWN DIALOGUES.
        YOU MUST RETAIN URLS AS IT IS.
        YOU MUST BE CONCISE YET PRECISE.
        YOU MUST OUTPUT IN PROPERLY ANNOTATED MARKDOWN FORMAT.

        SEARCH QUERY:
        {query}

        WEBPAGE TEXT:
        {text}
    """


app = FastAPI(
    title="Web Search API",
    description="API for searching web pages using Brave Search API. returns raw text of the page.",
    version="0.1.0",
)


class SearchRequest(BaseModel):
    q: str = Field(description="Search query (natural language)")
    url: Optional[str] = Field(
        None, description="Optional: Direct URL to fetch instead of search"
    )
    search_context: str = Field(
        "",
        description="Optional: Natural language description of what to look for in the pages",
    )
    n: int = Field(3, description="Number of pages to return", ge=1, le=15)


class PageResult(BaseModel):
    url: str = Field(..., description="URL of the page")
    page_title: str = Field("", description="Title of the page")
    page_contents: str = Field(..., description="Contents of the page")


class SearchResponse(BaseModel):
    results: List[PageResult] = Field(..., description="List of search results")


@app.post("/search", response_model=SearchResponse)
async def search(
    body: SearchRequest, x_brave_search_api_key: Annotated[str | None, Header()] = None
):
    async def fetch_url_content(
        url: str, client: httpx.AsyncClient
    ) -> Optional[PageResult]:
        try:
            page_response = await client.get(url, timeout=5.0, follow_redirects=True)
            page_response.raise_for_status()

            soup = BeautifulSoup(page_response.text, "html.parser")

            page_title = ""
            title_tag = soup.find("title")
            if title_tag and title_tag.string:
                page_title = title_tag.string.strip()

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]

                if href.startswith("/"):
                    if href.startswith("//"):
                        href = "https:" + href
                    else:
                        base_url = "/".join(url.split("/")[:3])
                        href = base_url + href

                link_text = a_tag.get_text(strip=True)
                if not link_text:
                    link_text = "Link"

                cleaned_href = re.sub(r"^https?://", "", href)
                a_tag.string = f"{link_text} ({cleaned_href})"

            for tag in soup(
                [
                    "meta",
                    "footer",
                    "nav",
                    "script",
                    "style",
                    "button",
                    "form",
                ]
            ):
                tag.extract()

            for stylesheet in soup.find_all("link", rel="stylesheet"):
                stylesheet.extract()

            text = soup.get_text(separator="\n", strip=True)

            if GEMINI_API_KEY:
                try:
                    print(f"Processing {url} with query: {body.search_context}")
                    prompt = get_prompt(text, body.q + "\n" + body.search_context)
                    response = await model.ainvoke(prompt)
                    processed_text = response.content
                    if processed_text:
                        text = processed_text
                    print(f"Processing complete for {url}")
                except Exception as e:
                    print(f"WARNING: Error processing with Gemini: {e}")

            return PageResult(url=url, page_title=page_title, page_contents=text)
        except Exception as e:
            print(f"WARNING: Error fetching {url}: {e}")
            return None

    if body.url:
        async with httpx.AsyncClient() as client:
            try:
                result = await fetch_url_content(body.url, client)
                if result:
                    return SearchResponse(results=[result])
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Unable to fetch content from URL: {body.url}",
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error fetching URL: {str(e)}"
                )

    if not body.q:
        raise HTTPException(
            status_code=400, detail="Either 'url' or 'q' parameter must be provided"
        )

    brave_api_key = x_brave_search_api_key or BRAVE_SEARCH_API_KEY

    if not brave_api_key:
        raise HTTPException(
            status_code=403,
            detail="Brave Search API key is needed.X-Brave-Search-API-Key header.",
        )

    async with httpx.AsyncClient() as client:
        try:
            brave_search_url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": brave_api_key,
            }
            params = {
                "q": body.q,
                "count": body.n,
            }

            search_response = await client.get(
                brave_search_url, headers=headers, params=params
            )
            search_response.raise_for_status()
            search_results = search_response.json()

            urls = []
            if "web" in search_results and "results" in search_results["web"]:
                urls = [
                    result["url"]
                    for result in search_results["web"]["results"][: body.n]
                ]

            if not urls:
                return SearchResponse(results=[])

            tasks = [fetch_url_content(url, client) for url in urls]
            results_with_none = await asyncio.gather(*tasks)

            results = [
                result
                for result in results_with_none
                if result is not None and result.page_contents.strip()
            ]

            return SearchResponse(results=results)

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error from Brave Search API: {e.response.text}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error during search: {str(e)}"
            )
