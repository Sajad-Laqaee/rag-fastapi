"""
utils.py:

Utility functions for handling embeddings, document ingestion, and text preprocessing
within a Retrieval-Augmented Generation (RAG) system.

This module provides helper methods to:
- Initialize and cache sentence embedding models.
- Connect to and manage persistent ChromaDB collections.
- Split text into overlapping chunks for better retrieval granularity.
- Extract and structure text content from PDF files with metadata.

All heavy or repeated operations (like embedding model loading) are optimized
using caching mechanisms.
"""

import os
import fitz  # PyMuPDF for PDF text extraction
import chromadb
from chromadb.utils import embedding_functions
from typing import List
from functools import lru_cache
import time
import hashlib


@lru_cache(maxsize=1)
def get_embedding_function():
    """
    Returns a cached instance of a sentence transformer embedding function.

    Uses the 'all-MiniLM-L6-v2' model for efficient and compact text embeddings.
    Caching ensures the model is loaded only once during runtime, significantly
    improving performance in repeated calls.

    Returns:
        embedding_functions.SentenceTransformerEmbeddingFunction:
            The embedding function instance.
    """
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )


def get_chroma_collection(collection_name: str = "RAG_Test_files"):
    """
    Connects to (or creates) a ChromaDB persistent collection for storing embeddings.

    Args:
        collection_name (str, optional): The name of the Chroma collection to use.
                                         Defaults to 'RAG_Test_files'.

    Returns:
        chromadb.api.models.Collection.Collection:
            A ChromaDB collection object ready for document storage and retrieval.
    """
    # Persistent client stores vector data in a local folder for durability
    chroma_client = chromadb.PersistentClient(path="chroma_VecDB")
    ef = get_embedding_function()
    return chroma_client.get_or_create_collection(
        name=collection_name,
        embedding_function=ef
    )


def split_text(text: str, chunk_size: int = 800, chunk_overlap: int = 20) -> List[str]:
    """
    Splits text into overlapping chunks for fine-grained retrieval.

    Args:
        text (str): The input text to split.
        chunk_size (int, optional): Number of characters per chunk. Default is 800.
        chunk_overlap (int, optional): Number of characters that overlap between chunks.
                                       Default is 20.

    Returns:
        List[str]: A list of text chunks.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        # Overlap ensures smoother semantic continuity between chunks
        start = end - chunk_overlap
    return chunks


def extract_text_from_pdf(pdf_path: str):
    """
    Extracts text from a PDF file and structures it into metadata-rich chunks.

    Each chunk is given a unique ID (SHA-1 hash) and includes metadata such as:
    - Source filename
    - Page number
    - Chunk index
    - Timestamp of ingestion

    Args:
        pdf_path (str): The absolute or relative path to the PDF file.

    Returns:
        List[dict]: A list of dictionaries, each representing a text chunk with metadata.
    """
    doc = fitz.open(pdf_path)
    all_chunks = []
    source_name = os.path.basename(pdf_path)

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if not text:
            continue  # Skip empty pages

        # Break text into paragraph-like units for more natural segmentation
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        for idx, chunk in enumerate(paragraphs):
            chunk_id = hashlib.sha1(
                f"{source_name}-{page_num}-{idx}-{time.time()}".encode()
            ).hexdigest()

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
