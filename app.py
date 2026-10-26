"""
Root Entrypoint (app.py) for Streamlit Community Cloud and cloud hosters.
Redirects to src.ui.app with environment path configuration.
"""
import os
import sys

# Linux SQLite compatibility shim for ChromaDB
try:
    __import__("pysqlite3")
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except Exception:
    pass

# Ensure repository root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Run main application
import src.ui.app
