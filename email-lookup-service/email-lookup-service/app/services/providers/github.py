import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Optional
from ..extractor import extract_emails_from_elements
from ...config import settings

HEADERS = {"User-Agent": "email-lookup-service/1.0"}

class GitHubProvider:
    name = "github"
    
    # Target specific HTML elements where user emails are likely to appear
    TARGET_SELECTORS = [
        'profile', 'bio', 'description', 'contact', 'about', 
        'user-info', 'profile-info', 'user-details', 'vcard'
    ]

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
                    email = data["email"].lower()
                    # Check if it's not a system email
                    if not any(blacklisted in email for blacklisted in ['noreply@', 'no-reply@', 'github@']):
                        return email
                # If blog URL exists, pass it back as hint
                blog = data.get("blog")
                if blog:
                    # Fetch and scrape it
                    try:
                        rb = await client.get(blog, headers=headers)
                        rb.raise_for_status()
                        emails = extract_emails_from_elements(rb.text, self.TARGET_SELECTORS)
                        if emails:
                            return emails[0]
                    except Exception:
                        pass
            # 2) Fallback to parsing the profile HTML for mailto links
            html_url = f"https://github.com/{username}"
            rh = await client.get(html_url, headers=headers)
            rh.raise_for_status()
            
            # Use targeted extraction first, then fallback to full page
            emails = extract_emails_from_elements(rh.text, self.TARGET_SELECTORS)
            
            # If no emails found in targeted areas, try full page extraction
            if not emails:
                emails = extract_emails_from_elements(rh.text)
            
            return emails[0] if emails else None
