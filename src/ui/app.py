import streamlit as st
import requests
import os

# Allow configuring the API host via environment variable, defaulting to localhost
API_HOST = os.getenv("API_HOST", "http://127.0.0.1:8000")

st.set_page_config(page_title="Smart Knowledge Base", layout="wide")
st.title("🧠 Smart Knowledge Base Agent")

with st.sidebar:
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Choose a file (PDF, DOCX, TXT)")
    if st.button("Upload"):
        if uploaded_file:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            try:
                res = requests.post(f"{API_HOST}/upload", files=files)
                if res.status_code == 200:
                    st.success("File uploaded and indexing started!")
                else:
                    st.error(f"Failed to upload: {res.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")
        else:
            st.warning("Please select a file first.")
            
st.header("Search")
query = st.text_input("Ask a question about your documents...")

if st.button("Search") and query:
    with st.spinner("Searching..."):
        try:
            res = requests.post(f"{API_HOST}/search", json={"query": query, "top_k": 5})
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
                
                if not results:
                    st.info("No matching results found.")
                else:
                    for i, r in enumerate(results):
                        # Extract just the filename if it's a path
                        source_name = os.path.basename(r['source_id'])
                        score = r['score']
                        with st.expander(f"Result {i+1} | Source: {source_name} | Distance: {score:.4f}"):
                            st.write(r['content'])
            else:
                st.error(f"Search failed: {res.text}")
        except Exception as e:
            st.error(f"Connection error: {e}")
