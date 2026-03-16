from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

_ALLOWED_SCHEMES = {"http", "https"}
_MAX_CONTENT_CHARS = 5000
_REQUEST_TIMEOUT = 15.0
_MAX_REDIRECTS = 5


def _is_safe_url(url: str) -> bool:
    """Reject non-HTTP(S) schemes to prevent SSRF."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in _ALLOWED_SCHEMES:
        return False

    hostname = parsed.hostname or ""
    if not hostname:
        return False

    return True


async def fetch_webpage_content(url: str) -> dict:
    """Fetch and extract the main text content from a webpage.

    Only fetches public HTTP/HTTPS URLs. Returns extracted text content
    suitable for use as LLM context.

    Args:
        url: The URL of the webpage to fetch content from.

    Returns:
        A dict with 'url', 'title', and 'content' keys.
        On failure, 'content' contains an error description.
    """
    if not _is_safe_url(url):
        return {
            "url": url,
            "title": "",
            "content": "Error: URL must use http or https scheme.",
        }

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            max_redirects=_MAX_REDIRECTS,
            timeout=_REQUEST_TIMEOUT,
        ) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "LearningPlatformBot/1.0"},
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        return {"url": url, "title": "", "content": "Error: Request timed out."}
    except httpx.TooManyRedirects:
        return {"url": url, "title": "", "content": "Error: Too many redirects."}
    except httpx.HTTPStatusError as e:
        return {
            "url": url,
            "title": "",
            "content": f"Error: HTTP {e.response.status_code}.",
        }
    except httpx.HTTPError:
        return {"url": url, "title": "", "content": "Error: Could not fetch URL."}

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type:
        return {
            "url": url,
            "title": "",
            "content": f"Error: Non-HTML content type ({content_type.split(';')[0]}).",
        }

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    text = soup.get_text(separator="\n", strip=True)

    if len(text) > _MAX_CONTENT_CHARS:
        text = text[:_MAX_CONTENT_CHARS] + "... [truncated]"

    if not text:
        return {"url": url, "title": title, "content": "No readable text found on page."}

    return {"url": url, "title": title, "content": text}
