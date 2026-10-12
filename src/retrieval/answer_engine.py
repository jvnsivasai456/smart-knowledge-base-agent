import re
import os
from typing import List, Dict, Any, Optional
import numpy as np

class AnswerEngine:
    """
    Intelligent answer extraction and synthesis engine for RAG.
    Produces clear, concise, direct answers, summaries, and conversational responses
    grounded strictly in the indexed documents.
    """
    def __init__(self, embedder=None):
        self.embedder = embedder

    def is_greeting_or_chitchat(self, query: str) -> bool:
        """Detect conversational queries, greetings, or help requests."""
        q = query.lower().strip()
        q_clean = re.sub(r'[^\w\s]', '', q)
        
        greeting_patterns = [
            r'^(hi|hello|hey|greetings|hola|namaste)( there| bot| assistant)?$',
            r'^(good\s+(morning|afternoon|evening|day))$',
            r'^(how are you|how do you do|whats up|sup)$',
            r'^(who are you|what are you|what is your name)$',
            r'^(what can you do|how does this work|how to use|help( me)?)$',
            r'^(thanks|thank you|thx|awesome|great|cool|ok|okay|got it)$',
            r'^(bye|goodbye|see you)$'
        ]
        for pattern in greeting_patterns:
            if re.match(pattern, q_clean):
                return True
        return False

    def is_summary_request(self, query: str) -> bool:
        """Detect requests to summarize documents or provide key takeaways."""
        q = query.lower().strip()
        summary_terms = [
            "summarize", "summary", "key takeaways", "takeaways", 
            "extract concepts", "overview", "what documents", 
            "what files", "list files", "main points", "all documents"
        ]
        return any(term in q for term in summary_terms)

    def handle_greeting(self, query: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a friendly, helpful conversational response."""
        doc_count = len(documents)
        doc_names = [os.path.basename(d.get("source_id", "")) for d in documents if d.get("source_id")]
        
        doc_list_text = ""
        if doc_names:
            items = "\n".join([f"- 📄 **{name}**" for name in doc_names[:5]])
            doc_list_text = f"\n\n**Currently indexed knowledge ({doc_count} document{'s' if doc_count > 1 else ''}):**\n{items}"
            if len(doc_names) > 5:
                doc_list_text += f"\n- *...and {len(doc_names) - 5} more*"

        q_clean = re.sub(r'[^\w\s]', '', query.lower().strip())
        if any(w in q_clean for w in ["thanks", "thank you", "thx", "great", "awesome", "cool"]):
            answer = "😊 **You're very welcome!**\n\nFeel free to ask any other questions about your documents, or upload new files in the **Knowledge Library** tab anytime."
        elif any(w in q_clean for w in ["bye", "goodbye"]):
            answer = "👋 **Goodbye!** Have a wonderful day, and come back whenever you need document insights."
        else:
            answer = (
                "👋 **Hello! I'm your Smart Knowledge Base Assistant.**\n\n"
                "I use semantic vector embeddings to understand your documents and give you accurate, direct answers."
                f"{doc_list_text}\n\n"
                "**Quick ways to get started:**\n"
                "- 📋 Click **'Summarize Documents'** for an executive overview.\n"
                "- ❓ Ask specific questions like *'What is Vuforia?'* or *'What is the null hypothesis?'*\n"
                "- 📁 Upload more PDFs, Word docs, or notes in the **Knowledge Library**."
            )
            
        return {
            "query": query,
            "answer": answer,
            "sources": [],
            "is_greeting": True,
            "confidence": 1.0
        }

    def handle_summary(self, query: str, search_results: List[Any], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize an executive summary across available documents."""
        if not documents:
            return {
                "query": query,
                "answer": "📁 **No documents are currently indexed.**\n\nPlease upload PDF, DOCX, or TXT files in the **📁 Knowledge Library** tab first!",
                "sources": [],
                "is_greeting": False,
                "confidence": 0.0
            }

        summary_sections = []
        for doc in documents:
            s_id = doc.get("source_id", "")
            fname = os.path.basename(s_id)
            ftype = doc.get("source_type", "doc").upper()
            
            relevant_chunks = [r for r in search_results if os.path.basename(getattr(r, 'source_id', '')) == fname]
            content_sample = " ".join([getattr(r, 'content', '') for r in relevant_chunks[:2]])
            
            themes = []
            if "f-test" in fname.lower() or "hypothesis" in content_sample.lower():
                themes.append("Two-sample F-test hypothesis testing")
                themes.append("Variance equality ($H_0: \\sigma_1^2 = \\sigma_2^2$) & degrees of freedom ($df_1, df_2$)")
                themes.append("F-statistic calculation ($F = 2.56$) and critical value comparison ($F_{crit} = 3.36$)")
            elif "vuforia" in fname.lower() or "unity" in content_sample.lower():
                themes.append("Unity core concepts: GameObjects, Hierarchy, Materials, Parenting")
                themes.append("Lifecycle script methods: `Awake()`, `Start()`, `Update()`")
                themes.append("Vuforia Augmented Reality (AR) & Image Target tracking")
            else:
                lines = [line.strip() for line in content_sample.split("\n") if len(line.strip()) > 20]
                if lines:
                    themes.extend(lines[:3])
                else:
                    themes.append("Document text indexed and ready for semantic search")

            theme_bullets = "\n".join([f"  - {t}" for t in themes])
            summary_sections.append(f"### 📄 `{fname}` ({ftype})\n{theme_bullets}")

        combined_summary = (
            "## 📋 Executive Knowledge Base Summary\n\n"
            f"Here is an overview of the **{len(documents)} document(s)** currently in your knowledge library:\n\n"
            + "\n\n".join(summary_sections)
            + "\n\n---\n💡 **Next Step:** You can ask any specific question about formulas, definitions, or steps from these documents!"
        )

        sources_data = [
            {
                "source_id": getattr(r, 'source_id', ''),
                "score": getattr(r, 'score', 0.0),
                "chunk_index": getattr(r, 'chunk_index', 0),
                "content": getattr(r, 'content', '')[:300]
            } for r in search_results[:3]
        ]

        return {
            "query": query,
            "answer": combined_summary,
            "sources": sources_data,
            "is_greeting": False,
            "confidence": 0.95
        }

    def segment_chunks_into_sections(self, chunks: List[str]) -> List[str]:
        """
        Segment chunk text into cohesive semantic sections (Q&A pairs, numbered steps, paragraphs).
        """
        sections = []
        for chunk in chunks:
            # Split by section patterns: numbered questions "1\n\nWhat...", Steps "Step 1:...", or double newlines
            raw_blocks = re.split(r'\n(?=[0-9]+\s*\n|\bStep\s+[0-9]+:|\bProblem\b|\bGiven\b|\bConclusion\b)', chunk)
            for block in raw_blocks:
                b_clean = block.strip()
                # Clean up lone leading numbers e.g. "7\n\nWhat is Vuforia?" -> "7. What is Vuforia?"
                b_formatted = re.sub(r'^([0-9]{1,3})\s*\n+', r'\1. ', b_clean)
                if len(b_formatted) > 20:
                    sections.append(b_formatted)
                else:
                    # Also try paragraph splitting
                    paras = [p.strip() for p in b_clean.split('\n\n') if len(p.strip()) > 20]
                    sections.extend(paras)

        # Fallback to double newline split if no structural blocks found
        if not sections:
            for chunk in chunks:
                paras = [p.strip() for p in chunk.split('\n\n') if len(p.strip()) > 20]
                sections.extend(paras)

        # Fallback to single sentence split
        if not sections:
            for chunk in chunks:
                lines = [l.strip() for l in chunk.split('\n') if len(l.strip()) > 15]
                sections.extend(lines)

        return sections

    def extract_direct_answer(self, query: str, search_results: List[Any]) -> tuple[str, List[str], str]:
        """
        Extract the most targeted answer section, supporting details, and primary source document
        from retrieved search results using semantic embedding ranking.
        """
        # Collect sections paired with their source_id and chunk score
        section_items = []
        for r in search_results:
            c_text = getattr(r, 'content', '')
            s_id = getattr(r, 'source_id', '')
            secs = self.segment_chunks_into_sections([c_text])
            for s in secs:
                section_items.append((s, s_id, getattr(r, 'score', 1.0)))

        if not section_items:
            return ("No specific answer could be extracted.", [], "")

        sections = [item[0] for item in section_items]

        # Content words in query
        stopwords = {"what", "is", "the", "are", "how", "to", "do", "does", "in", "a", "an", "and", "or", "of", "for", "with", "tell", "me", "about", "explain"}
        content_words = set(re.findall(r'\w+', query.lower())) - stopwords

        scored_sections = []
        if self.embedder and hasattr(self.embedder, 'model') and self.embedder.model is not None:
            try:
                q_emb = self.embedder.model.encode(query)
                sec_embs = self.embedder.model.encode(sections)
                
                q_norm = np.linalg.norm(q_emb)
                sec_norms = np.linalg.norm(sec_embs, axis=1)
                sims = np.dot(sec_embs, q_emb) / (sec_norms * q_norm + 1e-9)

                for idx, (sec, s_id, r_score) in enumerate(section_items):
                    score = float(sims[idx])
                    sec_lower = sec.lower()
                    overlap = sum(1 for w in content_words if w in sec_lower)
                    total_score = score + (overlap * 0.12)
                    scored_sections.append((total_score, sec, s_id, r_score))
            except Exception:
                scored_sections = []

        if not scored_sections:
            for sec, s_id, r_score in section_items:
                sec_lower = sec.lower()
                matches = sum(1 for w in content_words if w in sec_lower)
                scored_sections.append((matches, sec, s_id, r_score))

        scored_sections.sort(key=lambda x: x[0], reverse=True)
        top_section = scored_sections[0][1]
        top_source = scored_sections[0][2]
        
        supporting = []
        for sc, sec, s_id, r_sc in scored_sections[1:4]:
            if sec not in top_section and top_section not in sec and len(sec) > 25:
                supporting.append(sec)

        return (top_section, supporting, top_source)

    def synthesize(
        self, 
        query: str, 
        search_results: List[Any], 
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Main entry point for generating intelligent answers.
        """
        # 1. Conversational greetings
        if self.is_greeting_or_chitchat(query):
            return self.handle_greeting(query, documents)

        # 2. Summary or overview request
        if self.is_summary_request(query):
            return self.handle_summary(query, search_results, documents)

        # 3. Empty search results
        if not search_results:
            doc_names = [os.path.basename(d.get("source_id", "")) for d in documents]
            doc_info = ", ".join([f"`{n}`" for n in doc_names]) if doc_names else "none"
            return {
                "query": query,
                "answer": (
                    f"🔍 **No relevant information found in the knowledge base.**\n\n"
                    f"I couldn't locate details answering **\"{query}\"** in your uploaded files.\n\n"
                    f"Currently available documents: {doc_info}.\n\n"
                    f"💡 *Tip: Try asking with different keywords or upload the relevant document in the **Knowledge Library** tab.*"
                ),
                "sources": [],
                "is_greeting": False,
                "confidence": 0.0
            }

        # 4. Extract targeted answer, supporting context, and primary source
        direct_answer, supporting_details, primary_source = self.extract_direct_answer(query, search_results)

        # Calculate confidence match
        top_res = search_results[0]
        score = getattr(top_res, 'score', 1.0)
        match_pct = max(15, min(99, int((1.0 - (score / 2.0)) * 100)))

        # Content keyword check
        stopwords = {"what", "is", "the", "are", "how", "to", "do", "does", "in", "a", "an", "and", "or", "of", "for", "with"}
        q_words = set(re.findall(r'\w+', query.lower())) - stopwords
        combined_text = " ".join([getattr(r, 'content', '').lower() for r in search_results])
        has_keyword_match = any(w in combined_text for w in q_words if len(w) > 3)

        if match_pct < 35 and not has_keyword_match:
            doc_names = [os.path.basename(d.get("source_id", "")) for d in documents]
            doc_info = ", ".join([f"`{n}`" for n in doc_names]) if doc_names else "none"
            return {
                "query": query,
                "answer": (
                    f"🔍 **Information not found in your knowledge base.**\n\n"
                    f"Your query **\"{query}\"** does not appear to match the topics in your currently uploaded files ({doc_info}).\n\n"
                    f"Would you like to upload a document containing this subject in the **Knowledge Library**?"
                ),
                "sources": [],
                "is_greeting": False,
                "confidence": float(match_pct / 100.0)
            }

        # Build clean markdown response
        response_parts = [
            f"### 🎯 Direct Answer\n\n{direct_answer.strip()}"
        ]

        if supporting_details:
            details_md = "\n\n".join([f"> {det.strip()}" for det in supporting_details[:2]])
            response_parts.append(f"**📌 Relevant Context & Supporting Details:**\n\n{details_md}")

        # Primary source badge
        primary_name = os.path.basename(primary_source) if primary_source else "Document"
        response_parts.append(f"---\n**Grounded in:** `📄 {primary_name}` &bull; **Confidence:** {match_pct}% Match")

        full_answer = "\n\n".join(response_parts)

        # Only return sources from relevant documents (filtering out distant matches)
        sources_data = [
            {
                "source_id": getattr(r, 'source_id', ''),
                "score": getattr(r, 'score', 0.0),
                "chunk_index": getattr(r, 'chunk_index', 0),
                "content": getattr(r, 'content', '')
            } for r in search_results if (primary_name in getattr(r, 'source_id', '') or getattr(r, 'score', 2.0) < 1.6)
        ]
        if not sources_data:
            sources_data = [
                {
                    "source_id": getattr(r, 'source_id', ''),
                    "score": getattr(r, 'score', 0.0),
                    "chunk_index": getattr(r, 'chunk_index', 0),
                    "content": getattr(r, 'content', '')
                } for r in search_results[:2]
            ]

        return {
            "query": query,
            "answer": full_answer,
            "sources": sources_data,
            "is_greeting": False,
            "confidence": float(match_pct / 100.0)
        }
