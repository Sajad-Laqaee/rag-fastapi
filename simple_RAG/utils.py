import os
import fitz
import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime
from typing import List, Dict
from functools import lru_cache
import time
import hashlib


@lru_cache(maxsize=1)
def get_embedding_function():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )


def get_chroma_collection(collection_name: str = "RAG_Test_files"):
    chroma_client = chromadb.PersistentClient(path="chroma_VecDB")
    ef = get_embedding_function()
    return chroma_client.get_or_create_collection(
        name=collection_name,
        embedding_function=ef
    )


def split_text(text: str, chunk_size: int = 800, chunk_overlap: int = 20) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - chunk_overlap
    return chunks


def load_documents_from_directory(directory_path: str) -> List[Dict[str, str]]:
    documents = []
    for filename in os.listdir(directory_path):
        full_path = os.path.join(directory_path, filename)
        if not os.path.isfile(full_path):
            continue

        file_date = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d")

        if filename.lower().endswith(".txt"):
            with open(full_path, "r", encoding="utf-8") as f:
                text = f.read()
            documents.append({
                "id": filename,
                "text": text,
                "source": filename,
                "date": file_date,
                "path": full_path
            })

        elif filename.lower().endswith(".pdf"):
            documents.append({
                "id": filename,
                "text": "",
                "source": filename,
                "date": file_date,
                "path": full_path
            })

    return documents

def extract_text_from_pdf(pdf_path):

    doc = fitz.open(pdf_path)
    all_chunks = []
    source_name = os.path.basename(pdf_path)

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if not text:
            continue

        # Split into smaller logical chunks
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for idx, chunk in enumerate(paragraphs):
            chunk_id = hashlib.sha1(f"{source_name}-{page_num}-{idx}-{time.time()}".encode()).hexdigest()
            all_chunks.append({
                "id": chunk_id,
                "content": chunk,
                "metadata": {
                    "source": source_name,
                    "page_number": page_num,
                    "chunk_index": idx,
                    "date_added": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
            })
    return all_chunks


