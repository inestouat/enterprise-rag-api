# DocIQ — Enterprise RAG System

Retrieval-Augmented Generation (RAG) system featuring hybrid search, cross-encoder reranking, confidence scoring, and grounded citations. Designed to run fully locally.


## What This Is

Most RAG tutorials stop at simple examples that call an LLM API in a few lines of code. DocIQ goes beyond that and demonstrates how real-world document intelligence systems are built.

DocIQ is a full-stack document intelligence API built from scratch. It ingests PDF, DOCX, and TXT files, processes and indexes them using both keyword-based and semantic search, and retrieves relevant information using a hybrid strategy.

Retrieved results are improved using a neural cross-encoder reranker, ensuring only the most relevant context is passed to the language model. The system also computes a confidence score for each query and can refuse to answer when the retrieved information is insufficient or unreliable.

All responses are generated using a local LLM and are fully grounded in retrieved documents. Every answer includes traceable citations, ensuring transparency and verifiability.





## Features

- **Multi-format ingestion**: PDF, DOCX, TXT  
- **Semantic chunking**: RecursiveCharacterTextSplitter (800 chars, 150 overlap)  
- **Vector storage**: ChromaDB with cosine similarity  
- **Keyword search**: BM25Okapi (rank-bm25)  
- **Hybrid retrieval**: RRF combining BM25 + vector  
- **Neural reranking**: Cross-encoder (ms-marco-MiniLM-L-6-v2)  
- **Confidence scoring**: High / medium / low tiers  
- **IDK handling**: Refuses low-confidence answers (no hallucination)  
- **LLM generation**: Qwen2.5 via Ollama (local)  
- **Citation grounding**: Source + page number  
- **Evaluation**: 20-question dataset + LLM-as-judge  
- **REST API**: FastAPI (OpenAPI docs)  
- **Frontend**: Streamlit (dark UI)  




# Quickstart

## Prerequisites
- Python 3.11+
- Ollama installed and running

## 1. Clone and install
```bash
git clone https://github.com/YOUR_USERNAME/enterprise-rag-api.git
cd enterprise-rag-api

python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

## 2. Configure environment
```bash
cp .env.example .env
```

Edit `.env`:
```env
EMBEDDING_MODEL=all-MiniLM-L6-v2
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
CHUNK_SIZE=800
CHUNK_OVERLAP=150
```

## 3. Pull the LLM
```bash
ollama pull qwen2.5:3b
```

## 4. Start the API
```bash
python -m app.main
```

API docs: http://localhost:8000/docs

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

The initial retrieval uses bi-encoders (fast, approximate). The reranker uses a cross-encoder that jointly encodes query + document for more accurate relevance scoring  but only on the top-K candidates, keeping latency low.

### Why confidence scoring matters
Most RAG systems answer every question regardless of retrieval quality. DocIQ computes a composite confidence score from reranker outputs and refuses to generate when confidence is below threshold returning a structured response explaining what was searched and why no answer was found.
This eliminates hallucination on out-of-scope questions entirely (100% IDK accuracy on eval suite).



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
requests
streamlit
numpy
```

Install all:
```bash
pip install -r requirements.txt
```

