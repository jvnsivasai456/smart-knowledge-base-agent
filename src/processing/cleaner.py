import re

def clean_text(text: str) -> str:
    """
    Clean text while preserving natural paragraph breaks and indentation.
    """
    if not text:
        return ""
    # Standardize CRLF to LF
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Collapse 3+ newlines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Collapse multiple inline spaces/tabs to a single space
    lines = [re.sub(r'[ \t]{2,}', ' ', line).strip() for line in text.split('\n')]
    return '\n'.join(lines).strip()
