import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Optional
from ..extractor import extract_emails
from ...config import settings

HEADERS = {"User-Agent": "email-lookup-service/1.0"}

class GitHubProvider:
    name = "github"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.2, max=2),
           retry=retry_if_exception_type((httpx.HTTPError,)))
    async def lookup(self, *, username: str, **kwargs) -> Optional[str]:
        headers = dict(HEADERS)
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
        # 1) Try API for email field (often null)
        api_url = f"{settings.GITHUB_API_BASE.rstrip('/')}/users/{username}"
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            r = await client.get(api_url, headers=headers)
            if r.status_code == 200:
                data = r.json()
                if data.get("email"):
                    return data["email"].lower()
                # If blog URL exists, pass it back as hint
                blog = data.get("blog")
                if blog:
                    # Fetch and scrape it
                    try:
                        rb = await client.get(blog, headers=headers)
                        rb.raise_for_status()
                        emails = extract_emails(rb.text)
                        if emails:
                            return emails[0]
                    except Exception:
                        pass
            # 2) Fallback to parsing the profile HTML for mailto links
            html_url = f"https://github.com/{username}"
            rh = await client.get(html_url, headers=headers)
            rh.raise_for_status()
            emails = extract_emails(rh.text)
            return emails[0] if emails else None
