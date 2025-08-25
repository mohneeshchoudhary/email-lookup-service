import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ..extractor import extract_emails

COMMON_FEEDS = ["", "/feed", "/rss", "/atom.xml"]  # try root first, then common feeds

class BlogProvider:
    name = "blog"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.2, max=2),
           retry=retry_if_exception_type((httpx.HTTPError,)))
    async def lookup(self, *, username: str = "", blog_url: str | None = None, **kwargs) -> Optional[str]:
        if not blog_url:
            return None
        blog_url = blog_url.rstrip("/")
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            for suffix in COMMON_FEEDS:
                url = blog_url + suffix
                try:
                    r = await client.get(url)
                    if r.status_code >= 400:
                        continue
                    emails = extract_emails(r.text)
                    if emails:
                        return emails[0]
                except Exception:
                    continue
        return None
