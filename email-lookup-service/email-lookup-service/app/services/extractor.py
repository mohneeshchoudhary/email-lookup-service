import re
from email_validator import validate_email, EmailNotValidError

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

def extract_emails(text: str) -> list[str]:
    if not text:
        return []
    found = set(m.group(0) for m in EMAIL_REGEX.finditer(text))
    cleaned = []
    for e in found:
        # strip trailing punctuation
        STRIP_CHARS = " ,;:<>()[]{}\n\t\r\"'"
        # replace the buggy line with:
        e2 = e.strip(STRIP_CHARS)
        try:
            valid = validate_email(e2, check_deliverability=False).normalized
            cleaned.append(valid.lower())
        except EmailNotValidError:
            continue
    return sorted(set(cleaned))
