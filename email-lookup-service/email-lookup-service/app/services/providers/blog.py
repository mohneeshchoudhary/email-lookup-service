import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ..extractor import extract_emails_from_elements

COMMON_FEEDS = ["", "/feed", "/rss", "/atom.xml"]  # try root first, then common feeds

class BlogProvider:
    name = "blog"
    
    # Target specific HTML elements where user emails are likely to appear
    TARGET_SELECTORS = [
        'contact', 'about', 'author', 'profile', 'bio', 'description',
        'footer', 'sidebar', 'author-info', 'contact-info'
    ]

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
                    
                    # Use targeted extraction first, then fallback to full page
                    emails = extract_emails_from_elements(r.text, self.TARGET_SELECTORS)
                    
                    # If no emails found in targeted areas, try full page extraction
                    if not emails:
                        emails = extract_emails_from_elements(r.text)
                    
                    if emails:
                        return emails[0]
                except Exception:
                    continue
        return None
