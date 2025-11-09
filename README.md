# 🦾 RAG-FastAPI - Intelligent Document Query System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Latest-purple)](https://www.trychroma.com/)
[![Ollama](https://img.shields.io/badge/Ollama-LLM-orange)](https://ollama.ai/)

A production-ready Retrieval-Augmented Generation (RAG) system built with FastAPI, ChromaDB, and Ollama. This system enables intelligent document querying by combining semantic search with large language model capabilities.

Now includes a **simple web-based UI** for document upload and querying using JavaScript.

## 🌟 Features

- **📄 Multi-format Document Ingestion**: Support for PDF and text file uploads
- **🔍 Semantic Search**: Advanced vector-based document retrieval using ChromaDB
- **🤖 LLM Integration**: Powered by Ollama for intelligent response generation
- **🔐 Privacy-First**: Built-in anonymization for sensitive data (PII, emails, phone numbers)
- **⚡ High Performance**: Optimized with caching and efficient text chunking
- **📊 Metadata Filtering**: Query documents by source and page numbers
- **🖥️ Web UI**: Simple HTML + JavaScript interface for querying and uploading documents

## 🏗️ Architecture

```mermaid
graph TB
    A[Client / Web UI] -->|Upload Files| B[FastAPI Server]
    A -->|Query| B
    B -->|Process & Chunk| C[Text Processing]
    C -->|Generate Embeddings| D[SentenceTransformers]
    D -->|Store| E[ChromaDB Vector Store]
    B -->|Retrieve Context| E
    B -->|Generate Response| F[Ollama LLM]
    C -->|Optional| G[spaCy NER]
    
    style A fill:#f9f,stroke:#333,stroke-width:2px,color:#000
    style B fill:#bbf,stroke:#333,stroke-width:2px,color:#000
    style E fill:#bfb,stroke:#333,stroke-width:2px,color:#000
    style F fill:#fbf,stroke:#333,stroke-width:2px,color:#000
````

---

## 📋 Prerequisites

* **Python 3.8** or higher
* **Ollama API access** (for LLM inference)
* **4GB+ RAM** recommended
* **Optional:** CUDA-capable GPU for faster embeddings
* **Web browser** for UI

---

## 🚀 Quick Start

### 1️⃣ Clone the Repository

```ini
git clone https://github.com/yourusername/rag-fastapi.git
cd rag-fastapi
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Set Up Environment Variables

Create a `.env` file in the project root:

```ini
OLLAMA_API_KEY=your_ollama_api_key_here
OLLAMA_MODEL="deepseek-v3.1:671b-cloud"  # or another model
```

### 4️⃣ Run the Application

```bash
uvicorn main_fastapi:app --reload
```

* API and web UI are available at: [http://localhost:8000](http://localhost:8000)
* Swagger UI for testing: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🖥️ Web UI

A simple frontend is included to interact with the API:

**Features:**

* Upload PDF and text files
* Send natural language queries
* Display answers and sources directly in the browser

---

## 🔧 Configuration 
### **Text Processing Parameters** (in utils.py) 

* chunk_size: Size of text chunks (default: 800 characters)
* chunk_overlap: Overlap between chunks (default: 20 characters)

### **Embedding Model** Default: all-MiniLM-L6-v2. 
To change:
```python
# utils.py
embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="your-preferred-model"
)
```

### **LLM Model** 
Set via environment variable:
```ini
OLLAMA_MODEL=deepseek-v3.1:671b-cloud1 #you could change this to another llm
```

--- 
## 🛡️ Security Features 
### **Data Anonymization** 
Automatically redacts sensitive data: 
* 📧 Email addresses
* 📱 Phone numbers
* 💳 Credit card numbers
* 🏠 Physical addresses
* 🆔 Named entities (using spaCy)

--- 
## ⚡ Notes 
* A simple version without FastAPI is available in the simple_RAG folder for quick testing.
* You can use it as a reference for embedding and querying before deploying the API.
* **Usage order:**
```bash
# First, run to store your data in the vector database
python ingest_data.py

# Then, run to test your queries
python query_engine.py
```
