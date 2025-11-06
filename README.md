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

## 📂 Project Structure
├── main_fastapi.py         # FastAPI backend with endpoints
├── utils.py                # PDF/TXT processing, embeddings, helpers
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
└── docs/
    └── API.md              # separate API reference

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

