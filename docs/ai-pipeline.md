# AI Pipeline Architecture & Workflow

This document details the AI document processing, vector embedding, and Grounded RAG architecture.

## Pipeline Lifecycle Overview

```text
Uploaded Document (PDF / Image)
             ↓
    1. Storage Download (Supabase Private Bucket)
             ↓
    2. OCR Stage (Tesseract Provider)
             ↓
    3. LLM Extraction Stage (Structured Driving Licence Output)
             ↓
    4. document_info Persistence
             ↓
    5. Text Cleaning & Overlapping Chunking
             ↓
    6. Batch Embedding Generation (OpenAI text-embedding-3-small)
             ↓
    7. Vector Storage (public.document_chunks with VECTOR(1536))
             ↓
    8. Grounded RAG Q&A (pgvector Cosine Retrieval + Citation Prompt)
```

---

## Stage Details

### Stage 1: OCR Text Extraction (`app/services/ocr/`)
* **Interface**: `BaseOCRProvider` (abstract base class).
* **Provider**: `TesseractOCRProvider` (uses `pytesseract` and `pdf2image`).
* **Output**: `OCRResult` containing full raw text and page-wise text metadata.

### Stage 2: LLM Information Extraction (`app/services/llm/`)
* **Interface**: `BaseLLMProvider` (abstract base class).
* **Provider**: `OpenAILLMProvider` (uses OpenAI `gpt-4o-mini` with structured Pydantic outputs).
* **Output**: `DrivingLicenceExtraction` schema containing licence number, full name, dates, address, blood group, restrictions.
* **Persistence**: Saved to `public.document_info` via `document_info_repository`.

### Stage 3: Text Cleaning & Chunking (`app/services/chunking/` & `chunking_service.py`)
* **Cleaner**: `TextCleaner` strips noise, normalizes line breaks, and sanitizes characters.
* **Chunker**: `TextChunker` creates sliding-window chunks (default size: 500 characters, overlap: 50 characters) preserving page number origin.
* **Persistence**: Saved to `public.document_chunks` via `document_chunk_repository`.

### Stage 4: Embedding Generation (`app/services/embeddings/` & `embedding_service.py`)
* **Interface**: `BaseEmbeddingProvider`.
* **Provider**: `OpenAIEmbeddingProvider` (`text-embedding-3-small` / mock fallback).
* **Output**: 1536-dimensional dense floating-point vector.
* **Persistence**: Stored in `document_chunks.embedding` (`VECTOR(1536)`).

### Stage 5: Grounded RAG Q&A (`app/services/rag_service.py`)
* **Retrieval**: Uses `pgvector` distance operator `<=>` (cosine distance) to find top-k relevant chunks (`1 - cosine_distance`).
* **Prompt Engineering**: Inserts retrieved chunks as structured sources into a system prompt requiring strict factual grounding.
* **Response**: Returns clear answer string accompanied by exact page citations and source snippets.
