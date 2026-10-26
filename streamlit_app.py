"""
Streamlit Community Cloud Root Entrypoint for Smart Knowledge Base Agent.

This file ensures seamless deployment on Streamlit Cloud, Hugging Face Spaces,
or Docker containers by:
1. Shimming sqlite3 with pysqlite3 on Linux if needed for ChromaDB.
2. Setting the repository root in sys.path.
3. Invoking the main Streamlit application in src.ui.app.
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
