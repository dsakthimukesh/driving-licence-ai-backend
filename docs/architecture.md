# Production-Standard Layered Architecture

## Overview

This project is built using a clean, production-oriented, function-based layered architecture:

```text
Routes → Controllers → Services → Repositories → Database
```

## Layer Responsibilities

### 1. Routes (`app/routes/`)
* **Role**: Define HTTP endpoints, paths, verbs, request/response models, and OpenAPI tags.
* **Responsibilities**:
  * Apply FastAPI security dependencies (`get_current_user`).
  * Delegate requests directly to controllers.
  * Keep routes thin with zero business logic or database queries.

### 2. Controllers (`app/controllers/`)
* **Role**: Orchestrate HTTP-level request/response handling.
* **Responsibilities**:
  * Receive validated request models, DB session, and authenticated user.
  * Invoke corresponding service layer functions.
  * Catch domain exceptions (`AppException`) and translate them into standardized FastAPI `HTTPException` responses (e.g. 400, 401, 404, 409, 500).

### 3. Services (`app/services/`)
* **Role**: Pure business logic and workflow orchestration.
* **Responsibilities**:
  * Execute application workflows (e.g., user registration, pre-signed upload URL generation, document processing pipeline, chunking, embeddings, RAG retrieval).
  * Interact with data repositories and external provider abstractions.
  * Raise clean domain-level exceptions (`app/core/exceptions.py`).
  * Use function-based modules wherever practical.

### 4. Repositories (`app/repositories/`)
* **Role**: Encapsulate all database access queries.
* **Responsibilities**:
  * Execute SQLAlchemy 2.x ORM queries (`select()`, `db.add()`, `db.commit()`, `db.refresh()`, `db.delete()`).
  * Explicitly accept `db: Session` as the first parameter.
  * Contain zero business logic or HTTP framework exceptions.
  * Perform vector similarity queries using `pgvector` (`1 - cosine_distance`).

### 5. Database (`app/models/` & PostgreSQL)
* PostgreSQL schema managed via SQLAlchemy 2.x declarative models:
  * `public.users`
  * `public.documents`
  * `public.document_info`
  * `public.document_chunks` (with `VECTOR(1536)` embedding column)

---

## Why Function-Based Architecture?

* **Simplicity & Readability**: Functional code is straightforward, eliminating unnecessary class boilerplate (`self`, staticmethod wrappers).
* **Testability**: Pure functions taking explicit parameters (such as `db: Session`) are effortless to mock and unit test.
* **Separation of Provider Abstractions**: Classes are retained strictly where dynamic runtime substitution is beneficial (e.g., `BaseOCRProvider`, `BaseLLMProvider`, `BaseEmbeddingProvider`).
