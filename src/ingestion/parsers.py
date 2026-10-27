import hashlib
import requests
from bs4 import BeautifulSoup
import PyPDF2
import docx

def compute_hash(content: bytes) -> str:
    """Compute SHA-256 hash of the content."""
    return hashlib.sha256(content).hexdigest()

def parse_txt(file_path: str) -> tuple[str, str]:
    """Parse a plain text file."""
    with open(file_path, 'rb') as f:
        content = f.read()
    return content.decode('utf-8', errors='ignore'), compute_hash(content)

def parse_pdf(file_path: str) -> tuple[str, str]:
    """Parse a PDF file using PyPDF2."""
    text = ""
    with open(file_path, 'rb') as f:
        content = f.read()
        f.seek(0)
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text, compute_hash(content)

def parse_docx(file_path: str) -> tuple[str, str]:
    """Parse a DOCX file using python-docx."""
    with open(file_path, 'rb') as f:
        content = f.read()
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text, compute_hash(content)

def parse_html(url: str) -> tuple[str, str]:
    """Fetch and parse an HTML page."""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    content = response.content
    
    soup = BeautifulSoup(content, 'html.parser')
    # Remove scripts and styles
    for script in soup(["script", "style"]):
        script.extract()
        
    text = soup.get_text(separator='\n')
    # Simple whitespace cleanup
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return text, compute_hash(content)

def parse_local_html(file_path: str) -> tuple[str, str]:
    """Parse a local HTML file."""
    with open(file_path, 'rb') as f:
        content = f.read()
    soup = BeautifulSoup(content, 'html.parser')
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text(separator='\n')
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text, compute_hash(content)
