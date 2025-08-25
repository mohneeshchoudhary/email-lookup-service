import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Optional
from ..extractor import extract_emails
from ...config import settings

HEADERS = {"User-Agent": "email-lookup-service/1.0"}

class HuggingFaceProvider:
    name = "huggingface"

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
            emails = extract_emails(r.text)
            return emails[0] if emails else None
