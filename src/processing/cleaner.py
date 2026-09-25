import re

def clean_text(text: str) -> str:
    """Basic text cleaning."""
    # Remove multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove excessive spaces
    text = re.sub(r' {2,}', ' ', text)
    # Strip leading/trailing whitespace
    return text.strip()
