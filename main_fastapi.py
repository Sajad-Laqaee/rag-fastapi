"""
main_fastapi.py:c

FastAPI-based RAG (Retrieval-Augmented Generation) backend.

This module implements:
1. Document ingestion via PDF/TXT upload into a local ChromaDB vector store.
2. Semantic querying using embeddings + context retrieval.
3. Response generation using an Ollama-hosted large language model (LLM).
4. Optional anonymization and filtering to protect sensitive information.

It combines:
- FastAPI for REST endpoints
- ChromaDB for local vector storage and retrieval
- SentenceTransformers for text embeddings
- Ollama for LLM-based reasoning
- Optional spaCy for named entity anonymization

The endpoints:
    /ingest → Uploads and processes documents into ChromaDB
    /query  → Queries stored documents, retrieves semantic context, and generates an answer
"""

import os
import time
import hashlib
import tempfile
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
from ollama import Client

from utils import get_embedding_function, get_chroma_collection, split_text, extract_text_from_pdf


# ============================================================
# LOGGING CONFIGURATION
# ============================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# ENVIRONMENT AND LLM CLIENT
# ============================================================
load_dotenv()

# Retrieve credentials and model name from environment
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Create Ollama client for LLM inference
ollama_client = Client(
    host="https://ollama.com",
    headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"}
)


# ============================================================
# OPTIONAL SPACY NER FOR ANONYMIZATION
# ============================================================
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None


# ============================================================
# FASTAPI APP CONFIGURATION
# ============================================================
app = FastAPI(
    title="RAG with FastAPI",
    description="A lightweight RAG system using ChromaDB for vector storage and Ollama LLM for inference.",
    version="1.0"
)


# ============================================================
# Pydantic MODELS
# ============================================================

class IngestResponse(BaseModel):
    """Response schema for the /ingest endpoint."""
    inserted_chunks: int
    total_tokens_approx: int
    vector_dim: Optional[int]
    chunk_ids: List[str]


class QueryFilter(BaseModel):
    """Optional metadata filters for document queries."""
    source: Optional[str] = None
    min_page: Optional[int] = None
    max_page: Optional[int] = None


class QueryRequest(BaseModel):
    """Request schema for the /query endpoint."""
    question: str
    k: Optional[int] = 3
    score_threshold: Optional[float] = 0.6
    filter: Optional[QueryFilter] = None


class SourceItem(BaseModel):
    """Schema for a single retrieved source document snippet."""
    chunk_id: str
    source: Optional[str]
    page_number: Optional[int]
    date_added: Optional[str]
    similarity: float
    snippet: str


class QueryResponse(BaseModel):
    """Response schema containing LLM answer and supporting sources."""
    answer: str
    sources: List[SourceItem]


# ============================================================
# REGEX PATTERNS FOR DATA ANONYMIZATION
# ============================================================
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\b(\+?\d[\d\-\s]{6,}\d)\b")
CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
US_ZIP_RE = re.compile(r"\b\d{5}(?:-\d{4})?\b")
ADDRESS_EN_RE = re.compile(
    r"\d{1,5}\s+[A-Za-z0-9.\-]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct)\b",
    re.I
)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def make_chunk_id(source: str, page_number: Optional[int], idx: int) -> str:
    """Generate a unique, reproducible hash ID for a text chunk."""
    base = f"{source or 'unknown'}|{page_number or 0}|{idx}|{time.time()}"
    return hashlib.sha1(base.encode()).hexdigest()


def approx_token_count(text: str) -> int:
    """Roughly estimate token count by whitespace splitting."""
    return max(1, len(text.split()))


def anonymize_text(text: str) -> str:
    """
    Redact sensitive entities such as emails, phone numbers, and addresses.
    If spaCy is available, also replace PERSON, ORG, and LOCATION entities.
    """
    if not text:
        return text

    t = EMAIL_RE.sub("[EMAIL]", text)
    t = PHONE_RE.sub("[PHONE]", t)
    t = CREDIT_CARD_RE.sub("[CARD]", t)
    t = US_ZIP_RE.sub("[ZIP]", t)
    t = ADDRESS_EN_RE.sub("[ADDRESS]", t)

    if nlp:
        try:
            doc = nlp(t)
            for ent in sorted(doc.ents, key=lambda e: e.start_char, reverse=True):
                if ent.label_ in {"PERSON", "ORG", "GPE", "LOC", "FAC"}:
                    t = t[:ent.start_char] + f"[{ent.label_}]" + t[ent.end_char:]
        except Exception as e:
            logger.warning(f"spaCy anonymization failed: {e}")

    return t


# ============================================================
# ENDPOINT: DOCUMENT INGESTION
# ============================================================

@app.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(files: Optional[List[UploadFile]] = File(None)):
    """
    Upload and index PDF or text files into ChromaDB.

    Workflow:
      1. Accept uploaded files (PDF or plain text).
      2. Extract text content (via PyMuPDF for PDFs or direct read for TXT).
      3. Chunk text for retrieval granularity.
      4. Compute embeddings and store them in ChromaDB with metadata.

    Returns:
        IngestResponse: Summary of ingestion including number of chunks, token count, and IDs.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    collection = get_chroma_collection()
    ef = get_embedding_function()

    all_texts, all_ids, all_metadatas = [], [], []
    total_tokens = 0

    for f in files:
        filename = f.filename
        content_bytes = await f.read()

        try:
            # Handle PDF ingestion
            if filename.lower().endswith(".pdf"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(content_bytes)
                    tmp_path = tmp_file.name

                pdf_chunks = extract_text_from_pdf(tmp_path)
                os.remove(tmp_path)

                for i, chunk in enumerate(pdf_chunks):
                    chunk_id = chunk.get("id") or make_chunk_id(
                        chunk["metadata"]["source"],
                        chunk["metadata"]["page_number"],
                        i
                    )
                    all_texts.append(chunk["content"])
                    all_ids.append(chunk_id)
                    all_metadatas.append({
                        "source": chunk["metadata"]["source"],
                        "page_number": chunk["metadata"]["page_number"],
                        "chunk_id": chunk_id,
                        "date_added": datetime.now(timezone.utc).isoformat()
                    })
                    total_tokens += approx_token_count(chunk["content"])

            # Handle plain-text ingestion
            else:
                text = content_bytes.decode("utf-8", errors="ignore")
                chunks = split_text(text)
                for i, chunk in enumerate(chunks):
                    chunk_id = make_chunk_id(filename, None, i)
                    all_texts.append(chunk)
                    all_ids.append(chunk_id)
                    all_metadatas.append({
                        "source": filename,
                        "page_number": None,
                        "chunk_id": chunk_id,
                        "date_added": datetime.now(timezone.utc).isoformat()
                    })
                    total_tokens += approx_token_count(chunk)

        except Exception as e:
            logger.error(f"Failed processing {filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed processing {filename}: {e}")

    # Generate embeddings for all text chunks
    try:
        embeddings = ef(all_texts)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {e}")

    vector_dim = len(embeddings[0]) if embeddings else None

    # Persist embeddings and metadata into ChromaDB
    try:
        collection.upsert(
            ids=all_ids,
            documents=all_texts,
            embeddings=embeddings,
            metadatas=all_metadatas
        )
    except Exception as e:
        logger.error(f"Chroma upsert failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chroma upsert failed: {e}")

    return IngestResponse(
        inserted_chunks=len(all_ids),
        total_tokens_approx=total_tokens,
        vector_dim=vector_dim,
        chunk_ids=all_ids
    )


# ============================================================
# ENDPOINT: SEMANTIC QUERY + LLM RESPONSE
# ============================================================

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(req: QueryRequest):
    """
    Query ChromaDB using a natural-language question.

    Steps:
      1. Embed the user question.
      2. Retrieve top-k most semantically similar chunks.
      3. Optionally filter by metadata (source, page range).
      4. Send context + question to LLM for concise answering.
      5. Return both answer and supporting source snippets.
    """
    collection = get_chroma_collection()
    ef = get_embedding_function()

    # Step 1: Embed query
    try:
        q_emb = ef([req.question])[0]
    except Exception as e:
        logger.error(f"Query embedding failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query embedding failed: {e}")

    # Step 2: Apply optional filters
    metadata_filter = None
    if req.filter:
        if req.filter.source:
            metadata_filter = {"source": req.filter.source}
        elif req.filter.min_page is not None and req.filter.min_page == req.filter.max_page:
            metadata_filter = {"page_number": req.filter.min_page}

    # Step 3: Query ChromaDB
    try:
        n_results = req.k * 3 if req.filter else req.k
        results = collection.query(
            query_embeddings=[q_emb],
            n_results=n_results,
            include=["documents", "distances", "metadatas"],
            where=metadata_filter
        )
    except Exception as e:
        logger.warning(f"Chroma query with filter failed: {e}, retrying without filter")
        try:
            results = collection.query(
                query_embeddings=[q_emb],
                n_results=req.k,
                include=["documents", "distances", "metadatas"]
            )
        except Exception as e2:
            logger.error(f"Chroma query failed: {e2}")
            raise HTTPException(status_code=500, detail=f"Chroma query failed: {e2}")

    # Step 4: Post-process results
    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    filtered_items = []
    for doc, dist, meta in zip(docs, distances, metadatas):
        try:
            dist = float(dist)
        except:
            dist = 1.0
        if req.filter:
            page = meta.get("page_number")
            if req.filter.min_page and page is not None and page < req.filter.min_page:
                continue
            if req.filter.max_page and page is not None and page > req.filter.max_page:
                continue
        filtered_items.append((doc, meta, 1.0 - dist))

    # Apply similarity threshold
    final_items = [item for item in filtered_items if item[2] >= (req.score_threshold or 0.0)]
    if not final_items:
        final_items = filtered_items[:req.k]

    if not final_items:
        return QueryResponse(answer="No relevant context found.", sources=[])

    # Step 5: Build LLM prompt
    anonymized_context = "\n\n".join(anonymize_text(doc) for doc, _, _ in final_items)
    prompt = (
        "You are an assistant for question-answering. "
        "Use the retrieved context to answer concisely (<= 3 sentences). "
        "If the answer is not in the context, say 'I don't know'.\n\n"
        f"Context:\n{anonymized_context}\n\nQuestion:\n{req.question}"
    )

    # Step 6: Call Ollama LLM
    try:
        response = ollama_client.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])
        answer_text = response["message"]["content"]
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        answer_text = f"LLM call failed: {e}"

    # Step 7: Build final structured response
    sources = [
        SourceItem(
            chunk_id=meta.get("chunk_id", "N/A"),
            source=meta.get("source"),
            page_number=meta.get("page_number"),
            date_added=meta.get("date_added"),
            similarity=round(sim, 4),
            snippet=(doc[:400] + ("..." if len(doc) > 400 else ""))
        )
        for doc, meta, sim in final_items
    ]

    return QueryResponse(answer=answer_text, sources=sources)
