import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Optional
from ..extractor import extract_emails_from_elements
from ...config import settings

HEADERS = {"User-Agent": "email-lookup-service/1.0"}

class HuggingFaceProvider:
    name = "huggingface"
    
    # Target specific HTML elements where user emails are likely to appear
    TARGET_SELECTORS = [
        'profile', 'bio', 'description', 'contact', 'about', 
        'user-info', 'profile-info', 'user-details'
    ]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.2, max=2),
           retry=retry_if_exception_type((httpx.HTTPError,)))
    async def lookup(self, *, username: str, **kwargs) -> Optional[str]:
        # Public profile HTML page is easiest to parse for mailto links or plain text emails.
        url = f"{settings.HUGGINGFACE_BASE.rstrip('/')}/{username}"
        headers = dict(HEADERS)
        if settings.HUGGINGFACE_TOKEN:
            headers["Authorization"] = f"Bearer {settings.HUGGINGFACE_TOKEN}"
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
            
            # Use targeted extraction first, then fallback to full page
            emails = extract_emails_from_elements(r.text, self.TARGET_SELECTORS)
            
            # If no emails found in targeted areas, try full page extraction
            if not emails:
                emails = extract_emails_from_elements(r.text)
            
            return emails[0] if emails else None
