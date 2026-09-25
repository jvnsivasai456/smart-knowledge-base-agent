import os
from .document import RawDocument, DocumentMetadata
from .parsers import parse_txt, parse_pdf, parse_docx, parse_html

class Ingestor:
    def ingest_file(self, file_path: str) -> RawDocument:
        """Ingest a local file and return a RawDocument."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.txt':
            text, file_hash = parse_txt(file_path)
            source_type = 'txt'
        elif ext == '.pdf':
            text, file_hash = parse_pdf(file_path)
            source_type = 'pdf'
        elif ext in ['.docx', '.doc']:
            text, file_hash = parse_docx(file_path)
            source_type = 'docx'
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
            
        metadata = DocumentMetadata(
            source_id=file_path,
            source_type=source_type,
            file_hash=file_hash
        )
        return RawDocument(content=text, metadata=metadata)
        
    def ingest_url(self, url: str) -> RawDocument:
        """Ingest a web page and return a RawDocument."""
        text, file_hash = parse_html(url)
        metadata = DocumentMetadata(
            source_id=url,
            source_type='html',
            file_hash=file_hash
        )
        return RawDocument(content=text, metadata=metadata)
