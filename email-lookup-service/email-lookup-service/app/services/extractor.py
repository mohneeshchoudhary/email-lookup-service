import re
from email_validator import validate_email, EmailNotValidError

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# Common system emails to blacklist
SYSTEM_EMAIL_BLACKLIST = {
    'git@hf.co', 'noreply@', 'support@', 'help@', 'info@', 'admin@', 
    'webmaster@', 'postmaster@', 'abuse@', 'security@', 'no-reply@',
    'donotreply@', 'noreply@github.com', 'noreply@huggingface.co',
    'github@noreply.github.com', 'notifications@github.com',
    'git@github.com', 'github-actions@github.com'
}

def extract_emails(text: str) -> list[str]:
    if not text:
        return []
    found = set(m.group(0) for m in EMAIL_REGEX.finditer(text))
    cleaned = []
    for e in found:
        # strip trailing punctuation
        STRIP_CHARS = " ,;:<>()[]{}\n\t\r\"'"
        e2 = e.strip(STRIP_CHARS)
        
        # Skip if email is in blacklist
        if any(blacklisted in e2.lower() for blacklisted in SYSTEM_EMAIL_BLACKLIST):
            continue
            
        try:
            valid = validate_email(e2, check_deliverability=False).normalized
            cleaned.append(valid.lower())
        except EmailNotValidError:
            continue
    return sorted(set(cleaned))

def extract_emails_from_elements(html_content: str, target_selectors: list[str] = None) -> list[str]:
    """
    Extract emails from specific HTML elements using CSS selectors.
    Falls back to full page extraction if no selectors provided.
    """
    if not target_selectors:
        return extract_emails(html_content)
    
    # Simple HTML parsing to extract content from specific elements
    emails = []
    for selector in target_selectors:
        # Extract content that might contain the selector pattern
        # This is a simplified approach - in production you'd use BeautifulSoup
        pattern = re.compile(rf'<[^>]*class="[^"]*{selector}[^"]*"[^>]*>(.*?)</[^>]*>', re.DOTALL | re.IGNORECASE)
        matches = pattern.findall(html_content)
        for match in matches:
            emails.extend(extract_emails(match))
    
    # Also try to extract from the full content as fallback
    emails.extend(extract_emails(html_content))
    
    return sorted(set(emails))
