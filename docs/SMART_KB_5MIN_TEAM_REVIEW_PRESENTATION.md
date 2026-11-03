# Smart Knowledge Base Agent - 5-Minute Team Review Presentation

> **Autonomous Enterprise Hybrid RAG System with Zero-Downtime Indexing**  
> **Institution:** Sathyabama Institute of Science and Technology | Dept of CSE  
> **Internal Guide:** Ms. M. DEVIPRIYA | **HOD:** Dr. L. LAKSHMANAN, M.E., Ph.D.

---

## Slide 1 / 8

`	ext
SLIDE 1/8 SMART KNOWLEDGE BASE AGENT - PROJECT REVIEW TEAM OF 3 MEMBERS
Smart Knowledge Base Agent | 5-Minute Review Presentation for Internal Guide Ms. M. DEVIPRIYA Sathyabama Institute of Science and Technology | Dept of CSE
SMART KNOWLEDGE BASE AGENT
Autonomous Enterprise Hybrid RAG System with Zero-Downtime Indexing
5-Minute Viva & Review Presentation | Department of Computer Science & Engineering
Internal Guide: Ms. M. DEVIPRIYA  |  HOD: Dr. L. LAKSHMANAN, M.E., Ph.D.
MEMBER 1: SIVA SAI (44110216)
Role: Team Lead & Opening Speaker
Time Allocated: ~1.5 Minutes
- Welcome ma'am & introduce project.
- The Real-World Problem: Manual search is slow;
ChatGPT hallucinates & lacks private college data.
- Our Solution: Local AI Agent with cited answers.
- Frontend UI: Streamlit Web UI + Native Desktop App with
AI chat workspace & knowledge library table.MEMBER 2: BHARGAV (44110216)
Role: Architecture & Backend Lead
Time Allocated: ~1.5 to 2 Minutes
- System Architecture Diagram (Fig 4.1):
  Explains all 5 Tiers in simple words.
- Backend API: FastAPI on Port 8000.
- Hybrid Search: Vector Cosine + BM25 Keywords
combined with RRF (k=60).
- 0.62 Confidence Gate: Stops fake AI answers if question
is out-of-domain.MEMBER 3: KARTHIKEYA (44110202)
Role: Database & Working Demo Lead
Time Allocated: ~1.5 Minutes
- Dual Database Storage:
  1. ChromaDB: 61 dense 384-dim vectors.
  2. SQLite: metadata.sqlite with SHA-256 hashes.
- How It Works: 5-step operational lifecycle from upload to
cited answer.
- Zero Downtime: Background updates without server
restarts.
- Live Demonstration Walkthrough & Conclusion.
`

---

## Slide 2 / 8

`	ext
SLIDE 2/8 PROJECT INTRODUCTION & THE PROBLEM STATEMENT SPEAKER: SIVA SAI (44110216)
Smart Knowledge Base Agent | 5-Minute Review Presentation for Internal Guide Ms. M. DEVIPRIYA Sathyabama Institute of Science and Technology | Dept of CSESLIDE HIGHLIGHTS (KEY POINTS)
1. What is the Problem?
* In universities and companies, thousands of PDF/DOCX files exist (syllabi, notes,
timetables).
* Regular search (Ctrl+F) only looks for exact words and misses conceptual meaning.
* Public AI (ChatGPT) doesn't know our private college documents and often hallucinates
(makes up fake facts).
* Cloud AI leaks private data outside the institution.
2. What is our Solution?
* We built the Smart Knowledge Base Agent - a completely local, autonomous RAG
system.
* It reads college documents locally on our system.
* Answers student/staff questions in natural English.
* Strictly cites the document name and section so every answer can be verified 100%.SPOKEN SCRIPT (WHAT SIVA SAI SAYS TO MA'AM)
Speak clearly and confidently (1.5 Minutes):
"Good morning ma'am and respected examiners. I am Siva Sai (44110216), team lead.
Together with my teammates Bhargav and Karthikeya, we developed the Smart
Knowledge Base Agent.
In our college, we have many PDFs like timetables, 2-mark question banks, and course
materials. When students search, normal search fails if they don't type the exact word. If
they ask ChatGPT, it doesn't have access to our college files and gives wrong answers.
Our project solves this by creating a private AI assistant that runs right on our system. It
reads all our PDFs, understands the meaning of questions, and gives the exact answer
with the document citation.
Next, I will explain the Frontend interface that we designed for the users."
`

---

## Slide 3 / 8

`	ext
SLIDE 3/8 THE FRONTEND USER INTERFACE SPEAKER: SIVA SAI (44110216)
Smart Knowledge Base Agent | 5-Minute Review Presentation for Internal Guide Ms. M. DEVIPRIYA Sathyabama Institute of Science and Technology | Dept of CSEFRONTEND SPECIFICATIONS & SCREENS
Two Modes of Access Built:
1. Web Application: Built using Streamlit, accessible in browser on http://localhost:8501.
2. Native Windows Desktop App: Built using PyWebView (python desktop_app.py). Gives
a standalone, borderless Windows software window.
Key UI Components on Screen:
* AI Agent Chat Desk: Interactive search box with query suggestions.
* Clean Conversational AI Desk: Intuitive prompt bar with real-time semantic query answering.
* Knowledge Library Desk: Shows all 6 indexed files, types (PDF/DOCX), and chunk
numbers.
* Controls & Settings: Toggles between local offline synthesis and Gemini AI.SPOKEN SCRIPT (WHAT SIVA SAI SAYS TO MA'AM)
Spoken Script for Frontend (1 Minute):
"Ma'am, for our frontend, we wanted it to be simple and user-friendly for both teachers and
students. We built two interfaces:
First, a Web UI built with Streamlit running on port 8501. Second, a Desktop App using
PyWebView that opens as a native Windows window.
On the screen, users have three main tabs:
1. The AI Chat tab, where students and teachers can type any question in natural language to query their documents.
2. The Knowledge Library tab, which shows all active documents, file sizes, and chunk
numbers.
3. The Controls tab, which lets us configure natural language models including offline Local NLG, Claude, and Gemini.
Now, my teammate Bhargav will explain our System Architecture Diagram and the
Backend engine."
`

---

## Slide 4 / 8

`	ext
SLIDE 4/8 SYSTEM ARCHITECTURE DIAGRAM (FIGURE 4.1) SPEAKER: BHARGAV (44110216)
Smart Knowledge Base Agent | 5-Minute Review Presentation for Internal Guide Ms. M. DEVIPRIYA Sathyabama Institute of Science and Technology | Dept of CSESYSTEM ARCHITECTURE DIAGRAM (FIVE-TIER DESIGN)
Figure 4.1: Five-Tier System Architecture of Smart Knowledge Base AgentSPOKEN SCRIPT (WHAT BHARGAV SAYS TO MA'AM)
Explaining the Diagram in Simple English (1.5 Minutes):
"Good morning ma'am. I am Bhargav (44110216). I will explain our System Architecture
Diagram.
As shown in Figure 4.1, our project is organized into 5 simple, connected tiers:
* Tier 1 - Presentation Layer: This is the Streamlit screen where the user inputs questions.
* Tier 2 - API Routing Layer: Powered by FastAPI on port 8000. It receives the question and
sends it to our RAG engine.
* Tier 3 - Hybrid RAG Engine: This is the brain. It runs Vector Search and BM25 Keyword
Search together, merges the results using RRF (k=60), and checks the 0.62 Confidence
Gate.
* Tier 4 - Dual Database: ChromaDB stores 61 vector embeddings, while SQLite stores file
hashes and timestamps.
* Tier 5 - Background Ingestion: A continuous scanner that watches our uploads folder and
auto-indexes new files without stopping the server.
Next, I will explain how our Backend Search works."
`

---

## Slide 5 / 8

`	ext
SLIDE 5/8 THE BACKEND ENGINE & HYBRID SEARCH SPEAKER: BHARGAV (44110216)
Smart Knowledge Base Agent | 5-Minute Review Presentation for Internal Guide Ms. M. DEVIPRIYA Sathyabama Institute of Science and Technology | Dept of CSEBACKEND & SEARCH SPECIFICATIONS
1. FastAPI Server (main.py):
* Runs on Uvicorn on Port 8000.
* Provides 7 REST API routes (/chat, /search, /upload, /documents, /health).
* Includes live Swagger UI testing at http://localhost:8000/docs.
2. Hybrid Search (Vector + BM25):
* Vector Search: Uses all-MiniLM-L6-v2 (384 dimensions) to understand meaning.
* BM25 Search: Finds exact keywords, roll numbers, course codes.
* Reciprocal Rank Fusion (k=60): Combines both scores fairly without bias.
3. Confidence Gate (Threshold = 0.62):
* Prevents AI hallucinations. If top similarity is < 0.62, the system safely says 'Not found in
knowledge base'.SPOKEN SCRIPT (WHAT BHARGAV SAYS TO MA'AM)
Backend Spoken Script (1 Minute):
"Ma'am, for our backend, we used FastAPI with Python on port 8000.
The most important technical feature here is our Hybrid Search. If you do only Vector
search, it might miss exact words like 'Vuforia' or roll numbers. If you do only Keyword
search, it misses questions written in different words.
So we run both Vector search and BM25 search in parallel, and combine them using
Reciprocal Rank Fusion with constant k=60.
We also added a 0.62 Confidence Gate. If someone asks a question outside our
documents, like 'How to drive a car', the confidence is below 0.62. Our system politely
says 'Information not found' instead of inventing fake answers.
Now, my teammate Karthikeya will explain our Database layer and demonstrate how the
project works."
`

---

## Slide 6 / 8

`	ext
SLIDE 6/8 THE DUAL DATABASE STORAGE (CHROMADB + SQLITE) SPEAKER: KARTHIKEYA (44110202)
Smart Knowledge Base Agent | 5-Minute Review Presentation for Internal Guide Ms. M. DEVIPRIYA Sathyabama Institute of Science and Technology | Dept of CSEDATABASE ARCHITECTURE & FILES
Why Dual Database (Two Databases)?
A relational database cannot do fast vector search, and a vector database is not built for
relational metadata. So we separate concerns:
1. ChromaDB (Vector Store): data/chroma_db
* Stores 61 dense vector embeddings (384 numbers per chunk).
* Uses HNSW (Hierarchical Navigable Small World) index for sub-millisecond nearest
neighbor search.
2. SQLite Database: data/metadata.sqlite
* Tracks 6 documents in table 'files'.
* Stores SHA-256 cryptographic hashes and upload timestamps.
* Skips re-indexing unchanged documents in < 0.04s.SPOKEN SCRIPT (WHAT KARTHIKEYA SAYS TO MA'AM)
Database Spoken Script (1 Minute):
`

---

## Slide 7 / 8

`	ext
SLIDE 7/8 HOW THE PROJECT WORKS & LIVE DEMO SPEAKER: KARTHIKEYA (44110202)
Smart Knowledge Base Agent | 5-Minute Review Presentation for Internal Guide Ms. M. DEVIPRIYA Sathyabama Institute of Science and Technology | Dept of CSE5-STEP WORKING LIFECYCLE & LIVE DEMO
5-Step Operational Lifecycle:
1. Document Ingestion: PDF/Word files added to data/uploads/.
2. Hash Check: SQLite checks SHA-256 hash to prevent duplicates.
3. Text Chunking: Text split into 500-token chunks with 50-token overlap.
4. Embedding: Chunks converted to 384-dim vectors and saved to ChromaDB.
5. Gated Retrieval: User asks query -> Hybrid search retrieves top chunks -> Gated check
-> Grounded answer generated.
What to Show Ma'am During Demo:
* 1. Run Frontend: Double-click run_app.bat -> Type query -> Show cited answer.
* 2. Run Backend Docs: Open http://localhost:8000/docs -> Test GET /health.
* 3. Run Database Audit: In PowerShell run .\venv\Scripts\python.exe show_db.py.SPOKEN SCRIPT & CLOSING (KARTHIKEYA)
Closing Script (1 Minute):
"Ma'am, here is how the whole project works from start to finish:
When an administrator drops a new syllabus PDF into our uploads folder, our Directory
Scanner picks it up immediately. It splits the document into 500-token chunks, creates
384-dimensional vectors, and saves them into ChromaDB.
The best part is Zero Downtime: new files are indexed in the background without
restarting the server.
Now, let us show you the live running project:
1. We run run_app.bat to launch our frontend.
2. We type a question on screen to show the exact cited answer from our college document.
3. We show our Swagger API at port 8000.
4. And we run python show_db.py in terminal to prove our 61 vectors and 6 files in
ChromaDB and SQLite.
Thank you ma'am! We are now happy to answer your questions."
`

---

## Slide 8 / 8

`	ext
SLIDE 8/8 VIVA CHEAT-SHEET - QUICK ANSWERS FOR MA'AM ALL 3 MEMBERS PREPARATION
Smart Knowledge Base Agent | 5-Minute Review Presentation for Internal Guide Ms. M. DEVIPRIYA Sathyabama Institute of Science and Technology | Dept of CSEQ1: Why did you use two databases instead of one?
"Ma'am, SQLite is an ACID relational database perfect for file metadata and fast SHA-256 hash checking. ChromaDB is a specialized vector database with HNSW graph indexing for 384-dimensional
semantic search. Using both gives optimal speed and clean separation."
Q2: What is the 0.62 Confidence Gate and why is it needed?
"Ma'am, it stops AI hallucinations. If someone asks a question not in our documents, the similarity score is below 0.62. The system safely refuses to answer instead of making up false information."
Q3: What is RRF (Reciprocal Rank Fusion, k=60)?
"Ma'am, it is a mathematical formula that merges Vector Search results and BM25 Keyword Search results fairly, without needing manual weight tuning."
Q4: What is Zero Downtime Indexing?
"Ma'am, when a new PDF is added, our Directory Scanner indexes it in the background. The user can keep chatting and searching without turning off or restarting the server."
Q5: What embedding model are you using?
"We use sentence-transformers/all-MiniLM-L6-v2. It generates 384-dimensional dense vectors and runs fast locally on CPU in under 15 milliseconds per chunk."
`

---
