# DocIQ — Enterprise RAG System

> Production-grade Retrieval-Augmented Generation with hybrid search, OCR, cross-encoder reranking, and cited LLM answers.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-vector_store-FF6B35?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## What This Is



The  Enterprise Document Intelligence API  is a production-grade backend system that allows users to:

- Upload documents in any format: PDF (text-based or scanned), DOCX, TXT, PNG, JPG
- Automatically detect whether a PDF needs OCR (Optical Character Recognition)
- Extract, chunk, embed, and index document content into a hybrid search engine
- Ask natural language questions and receive accurate, cited answers powered by a local LLM **Every answer is traceable back to a source.**

The system is built entirely in Python, uses only open-source models, and runs fully locally — no OpenAI API key required, no data leaving your machine.




## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      DOCIQ PIPELINE                      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  INGESTION                                               │
│  Upload → Detect (text/scanned) → OCR if needed         │
│        → Chunk (overlap) → Embed → ChromaDB + BM25      │
│                                                          │
│  RETRIEVAL (Hybrid)                                      │
│  Query → BM25 (keyword) ──┐                              │
│       → Vector (semantic) ┴─→ RRF Fusion → Top-K        │
│                                                          │
│  RERANKING                                               │
│  Top-K → Cross-Encoder → Reordered by relevance         │
│                                                          │
│  GENERATION                                              │
│  Context → Qwen2.5 (Ollama) → Answer + Citations        │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Features

| Feature | Implementation |
|---|---|
| **Multi-format ingestion** | PDF, DOCX, TXT, PNG, JPG |
| **OCR support** | Tesseract via pytesseract — auto-detects scanned vs text-based PDFs |
| **Semantic chunking** | RecursiveCharacterTextSplitter with configurable overlap |
| **Vector storage** | ChromaDB with cosine similarity |
| **Keyword search** | BM25Okapi (rank-bm25) |
| **Hybrid retrieval** | RRF (Reciprocal Rank Fusion) combining BM25 + vector |
| **Neural reranking** | Cross-encoder (sentence-transformers) for precision |
| **LLM generation** | Qwen2.5 via Ollama — hallucination-resistant prompting |
| **Citation grounding** | Every answer links to source + page number |
| **REST API** | FastAPI with OpenAPI docs |
| **Frontend** | Streamlit  |


## Project Structure

```
enterprise-rag-api/
├── app/
│   ├── core/
│   │   └── config.py          # Settings from .env
│   ├── ingestion/
│   │   ├── ocr.py             # Tesseract OCR + scanned PDF detection
│   │   ├── parser.py          # PDF / DOCX / TXT parsers
│   │   ├── chunker.py         # Recursive text splitting
│   │   └── processor.py       # Full ingestion pipeline
│   ├── retrieval/
│   │   ├── bm25_index.py      # BM25 keyword index
│   │   ├── vector_store.py    # ChromaDB semantic search
│   │   ├── hybrid.py          # RRF fusion + reranking
│   │   └── reranker.py        # Cross-encoder reranker
│   ├── generation/
│   │   └── engine.py          # Ollama / Qwen2.5 generation
│   ├── ui/
│   │   └── streamlit_app.py   # Frontend UI
│   └── main.py                # FastAPI application
├── data/                      # ChromaDB storage (gitignored)
├── test_documents/            # Sample test files
├── tests/                     # Unit tests
├── .env.example               # Environment template
├── requirements.txt           # Dependencies
└── README.md
```



## Quickstart

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) installed and running
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed


### 1. Clone & install

```bash
git clone https://github.com/inestouat/enterprise-rag-api.git  
cd enterprise-rag-api


python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```


### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings
```

Key settings in `.env`:

```env
EMBEDDING_MODEL=all-MiniLM-L6-v2
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
CHUNK_SIZE=512
CHUNK_OVERLAP=64
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```


### 4. Start the API

```bash
python -m app.main
```

API docs available at: `http://localhost:8000/docs`

### 5. Start the UI (optional)

```bash
streamlit run app/ui/streamlit_app.py

```

UI available at: `http://localhost:8501`

---

## API Reference

### Health check

```http
GET /health
```

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "features": ["OCR", "Hybrid Retrieval", "Reranking", "Citations"],
  "components": {
    "ingestion": true,
    "retrieval": true,
    "generation": true
  }
}
```

## How the Retrieval Works

### Why hybrid search?

Neither pure keyword search nor pure semantic search is best alone:

- **BM25** excels at exact matches: product names, IDs, specific terminology
- **Vector search** excels at meaning: synonyms, paraphrases, conceptual queries

**RRF (Reciprocal Rank Fusion)** merges both ranked lists using the formula:

```
RRF_score = 1/(k + bm25_rank) + 1/(k + vector_rank)    where k=60
```

This is parameter-free, robust, and consistently outperforms weighted combinations.

### Why cross-encoder reranking?

The initial retrieval uses bi-encoders (fast, approximate). The reranker uses a cross-encoder that jointly encodes query + document for more accurate relevance scoring — but only on the top-K candidates, keeping latency low.


## Requirements

```
fastapi
uvicorn
pydantic
python-multipart
chromadb
sentence-transformers
rank-bm25
langchain-text-splitters
PyPDF2
python-docx
pytesseract
pdf2image
Pillow
requests
streamlit
```

Install all:
```bash
pip install -r requirements.txt
```



