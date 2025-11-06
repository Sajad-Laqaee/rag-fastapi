# 📄 Retrieval-Augmented Generation (RAG) System with FastAPI, ChromaDB & Ollama

A lightweight yet powerful Retrieval-Augmented Generation (RAG) backend for semantic search and question answering over private documents.  
Built with **FastAPI**, **ChromaDB**, **SentenceTransformers**, and **Ollama LLM**.

---

## 🚀 Features
- **Upload PDFs & TXT files** for ingestion  
- PDF text extraction via **PyMuPDF**  
- Chunking with overlap for high-quality semantic search  
- **Local persistent vector storage** using ChromaDB  
- **SentenceTransformers (MiniLM-L6-v2)** for embeddings  
- **Ollama LLM** integration for fast and concise answers  
- **Optional spaCy NER anonymization** for sensitive info  
- Metadata filtering for scoped queries

---

## 🛠 Tech Stack
- [FastAPI](https://fastapi.tiangolo.com/) – Modern Python API framework  
- [ChromaDB](https://docs.trychroma.com/) – Vector database for embeddings  
- [SentenceTransformers](https://www.sbert.net/) – State-of-the-art embeddings  
- [PyMuPDF](https://pymupdf.readthedocs.io/) – PDF parsing & text extraction  
- [Ollama](https://ollama.com/) – Local or cloud LLM inference engine  
- [spaCy](https://spacy.io/) – Named entity recognition (optional)

---

.
├── main_fastapi.py         # FastAPI backend with endpoints
├── utils.py                # PDF/TXT processing, embeddings, helpers
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
└── docs/
└── API.md              # separate API reference

yaml

---

## ⚙️ Installation

### Prerequisites
- Python **3.9+**
- [Ollama](https://ollama.com/) installed locally **OR** accessible via API
- `pip` for installing dependencies

### 1️⃣ Clone the repo
```bash
git clone https://github.com/your-username/your-rag-project.git
cd your-rag-project
2️⃣ Install dependencies
bash
pip install -r requirements.txt
Example requirements.txt:

ebnf
fastapi
uvicorn
chromadb
sentence-transformers
pymupdf
ollama
python-dotenv
spacy
3️⃣ Environment Variables
Create a .env file in your project directory:

ini
OLLAMA_API_KEY=your_api_key_here
OLLAMA_MODEL=llama3.2
4️⃣ Run the API
bash
uvicorn main_fastapi:app --reload
API available at:

dts
http://127.0.0.1:8000
📤 Document Ingestion
Endpoint:
POST /ingest

Upload and index PDF or text files into ChromaDB.

Workflow:

Accept uploaded files (PDF or .txt)
Parse and extract text
Split text into semantic chunks
Generate embeddings
Store embeddings with metadata in ChromaDB
Example Request (cURL):

bash
curl -X POST "http://127.0.0.1:8000/ingest" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@OpenAI.txt;type=text/plain" \
  -F "files=@document.pdf;type=application/pdf"
Response Example:

json
{
  "inserted_chunks": 23,
  "total_tokens_approx": 2668,
  "vector_dim": 384,
  "chunk_ids": [
    "20cf32899f67557eee483cc0b68d8fae566c8ea7",
    "379ba08fcc1598ddd83de35a2c11d5e764ac001d",
    "... more chunk IDs ..."
  ]
}
Response Fields:

inserted_chunks (int) — number of chunks stored
total_tokens_approx (int) — estimated token count
vector_dim (int) — embedding vector dimension
chunk_ids (array[string]) — SHA-1 IDs of stored chunks
🔍 Semantic Querying
Endpoint:
POST /query

Search over ingested content and answer using LLM.

Workflow:

Embed user question
Retrieve top-k relevant chunks from ChromaDB
Apply optional filters (filename, page range)
Send combined context + question to the LLM
Return answer + source snippets
Example Request (cURL):

bash
curl -X POST "http://127.0.0.1:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the partnership between OpenAI and Amazon?",
    "k": 5,
    "score_threshold": 0.6
  }'
Response Example:

json
{
  "answer": "OpenAI has signed a seven-year, $38 billion deal to buy cloud services from Amazon Web Services. This will give access to Nvidia processors for AI training.",
  "sources": [
    {
      "chunk_id": "8e788a9946275c7722a1622d80a0798fb2acbe85",
      "source": "OpenAI.txt",
      "page_number": null,
      "date_added": "2025-11-06T07:17:35.237897+00:00",
      "similarity": 0.6327,
      "snippet": "OpenAI turns to Amazon in $38 billion cloud services deal..."
    }
  ]
}
Response Fields:

answer (string) — concise LLM result
sources (array) — supporting snippets with:
chunk_id — unique chunk SHA-1 hash
source — original filename
page_number — PDF page number (if applicable)
date_added — ingestion timestamp
similarity — score between 0–1
snippet — excerpt of relevant content
📜 API Schemas
IngestResponse
json
{
  "inserted_chunks": 0,
  "total_tokens_approx": 0,
  "vector_dim": 0,
  "chunk_ids": ["string"]
}
QueryRequest
json
{
  "question": "string",
  "k": 0,
  "score_threshold": 0,
  "filter": {
    "source": "string",
    "min_page": 0,
    "max_page": 0
  }
}
QueryResponse
json
{
  "answer": "string",
  "sources": [
    {
      "chunk_id": "string",
      "source": "string",
      "page_number": 0,
      "date_added": "string",
      "similarity": 0,
      "snippet": "string"
    }
  ]
}
🛡️ Data Anonymization
Before sending context to the LLM, the system:

Masks emails, phone numbers, credit cards, ZIP codes, addresses
(Optional) Uses spaCy NER to anonymize names, orgs, and locations
📚 Testing the API
FastAPI provides interactive docs:

Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc
📜 License
MIT License – Free to use and modify with attribution.

🤝 Contributing
Pull requests, suggestions, and feature requests are welcome.

Fork the repo, make your changes, and submit a PR.

Author: Your Name

Version: 1.0

Last Updated: November 6, 2025

yaml

---

This README is:
- **Directly copy-paste ready**
- Combines **overview + install + usage + API reference**
- Matches your **actual FastAPI endpoints and responses**
- Professional enough for GitHub, corporate, or API documentation portals

---

If you want, I can also add **example Python client scripts** to the README so people can interact with `/ingest` and `/query` without using cURL, making onboarding even smoother.  
Do you want me to extend this README with **Python example usage**? That will make it even more complete.







---

## ⚙️ Installation

### Prerequisites
- Python **3.9+**
- [Ollama](https://ollama.com/)  accessible via API
- `pip` for installing dependencies


1️⃣ Clone the repo
```bash
git clone https://github.com/your-username/your-rag-project.git
cd your-rag-project

2️⃣ Install dependencies
bash
pip install -r requirements.txt

3️⃣ Environment Variables
Create a .env file in your project directory:
OLLAMA_API_KEY=your_api_key_here
OLLAMA_MODEL = "deepseek-v3.1:671b-cloud"

4️⃣ Run the API
uvicorn main_fastapi:app --reload
API available at:
http://127.0.0.1:8000

you can test it in:
http://127.0.0.1:8000/docs

