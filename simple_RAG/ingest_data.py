import os
from utils import (
    load_documents_from_directory,
    extract_text_from_pdf,
    split_text,
    get_embedding_function,
    get_chroma_collection,
)

def ingest_data():
    collection = get_chroma_collection()
    ef = get_embedding_function()

    documents = load_documents_from_directory("./data")
    if not documents:
        print("❌ No documents found.")
        return

    all_chunks = []
    print(f"📄 Found {len(documents)} documents. Splitting and extracting...")

    for doc in documents:
        path = doc.get("path")
        if not path or not os.path.exists(path):
            continue

        # Handle PDFs separately
        if path.lower().endswith(".pdf"):
            pdf_chunks = extract_text_from_pdf(path)
            all_chunks.extend(pdf_chunks)
        else:
            # Handle plain text
            chunks = split_text(doc["text"])
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc['id']}_chunk{i+1}"
                all_chunks.append({
                    "id": chunk_id,
                    "content": chunk,
                    "metadata": {
                        "source": doc["source"],
                        "page_number": None,
                        "chunk_index": i,
                        "date_added": doc["date"],
                    },
                })

    print(f"🔹 Total chunks: {len(all_chunks)}")

    print("⚙️ Generating embeddings in batches...")
    embeddings = ef([c["content"] for c in all_chunks])

    print("💾 Upserting into Chroma...")
    collection.upsert(
        ids=[c["id"] for c in all_chunks],
        documents=[c["content"] for c in all_chunks],
        embeddings=embeddings,
        metadatas=[c["metadata"] for c in all_chunks],
    )

    print("✅ Ingestion complete! Data (with metadata) stored in Chroma.")


if __name__ == "__main__":
    ingest_data()
