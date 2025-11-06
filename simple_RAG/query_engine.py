import os
from dotenv import load_dotenv
from ollama import Client
from utils import get_embedding_function, get_chroma_collection

# Load API keys and model name
load_dotenv()
API_KEY = os.getenv("OLLAMA_API_KEY")
MODEL = os.getenv("OLLAMA_MODEL")

client = Client(
    host="https://ollama.com",
    headers={'Authorization': f"Bearer {API_KEY}"}
)

def query(
    question: str,
    n_results: int = 3,
    score_threshold: float = 0.6,
    source_filter: str = None,
    min_page: int = None,
    max_page: int = None
):
    ef = get_embedding_function()
    collection = get_chroma_collection()

    query_embedding = ef([question])[0]

    # Build metadata filter for Chroma
    metadata_filter = {}
    if source_filter:
        metadata_filter["source"] = source_filter
    if min_page is not None or max_page is not None:
        metadata_filter["page_number"] = {}
        if min_page is not None:
            metadata_filter["page_number"]["$gte"] = min_page
        if max_page is not None:
            metadata_filter["page_number"]["$lte"] = max_page

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "distances", "metadatas"],
        where=metadata_filter if metadata_filter else None
    )

    retrieved_docs = results["documents"][0]
    retrieved_scores = results["distances"][0]
    retrieved_meta = results["metadatas"][0]

    # Convert distances to similarity
    similarities = [1 - d for d in retrieved_scores]

    # Filter by similarity threshold
    filtered_docs = [
        (doc, meta, sim)
        for doc, meta, sim in zip(retrieved_docs, retrieved_meta, similarities)
        if sim >= score_threshold
    ]

    if not filtered_docs:
        filtered_docs = list(zip(retrieved_docs, retrieved_meta, similarities))

    # Build context for LLM
    context = "\n\n".join([doc for doc, _, _ in filtered_docs])
    prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following retrieved context to answer the question. "
        "If the answer is not in the context, say you don't know. "
        "Keep the answer under three sentences.\n\n"
        f"Context:\n{context}\n\nQuestion:\n{question}"
    )

    response = client.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    answer = response["message"]["content"]

    print("\n================= ANSWER =================")
    print(answer)

    print("\n================= SOURCES =================")
    for i, (doc, meta, sim) in enumerate(filtered_docs):
        chunk_id = meta.get("chunk_id", "N/A")  # use metadata chunk_id
        page_info = f"Page {meta.get('page_number')}" if meta.get("page_number") else "N/A"
        print(f"\nSource {i+1} — {meta['source']} ({page_info}, Chunk ID: {chunk_id}, Date: {meta.get('date_added')}) — Similarity: {sim:.4f}")
        print(f"{doc[:400]}{'...' if len(doc) > 400 else ''}")

    print(f"\nSimilarity threshold: {score_threshold}")


if __name__ == "__main__":
    question = input("❓ Enter your question: ")

    # Ask if user wants metadata filtering
    apply_filters = input("🔹 Do you want to apply source/page filters? [y/n]: ").strip().lower()
    if apply_filters == "y":
        source_filter = input("📄 Filter by source (filename) [press Enter to skip]: ").strip() or None

        min_page_input = input("🔢 Minimum page number [press Enter to skip]: ").strip()
        min_page = int(min_page_input) if min_page_input else None

        max_page_input = input("🔢 Maximum page number [press Enter to skip]: ").strip()
        max_page = int(max_page_input) if max_page_input else None
    else:
        source_filter = None
        min_page = None
        max_page = None

    query(
        question,
        source_filter=source_filter,
        min_page=min_page,
        max_page=max_page
    )


