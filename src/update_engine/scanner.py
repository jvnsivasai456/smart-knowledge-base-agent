import os
import hashlib
from typing import Dict

def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file incrementally to handle large files."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

class DirectoryScanner:
    def __init__(self, directory: str):
        self.directory = directory
        
    def scan(self) -> Dict[str, str]:
        """Returns a dict mapping absolute file paths to their SHA256 hashes."""
        current_state = {}
        if not os.path.exists(self.directory):
            return current_state
            
        for root, _, files in os.walk(self.directory):
            for file in files:
                file_path = os.path.abspath(os.path.join(root, file))
                ext = os.path.splitext(file_path)[1].lower()
                
                # Only track supported document types
                if ext in ['.txt', '.pdf', '.docx', '.doc']:
                    file_hash = compute_file_hash(file_path)
                    current_state[file_path] = file_hash
                    
        return current_state
