# Interview Guide & Architecture Explanation

Use this document as a quick reference when explaining the backend architecture, design decisions, and future microservices roadmap during technical interviews.

## Key Talking Points

### 1. Architectural Choice: Layered Architecture
* **Question**: *Why did you choose a layered architecture (`Routes -> Controllers -> Services -> Repositories -> Database`)?*
* **Answer**:
  "I adopted a classic layered architecture to enforce a strict separation of concerns.
  - **Routes** manage HTTP endpoints and OpenAPI contracts.
  - **Controllers** orchestrate request handling and convert domain exceptions into standard HTTP error responses.
  - **Services** contain core business logic and AI pipeline workflows.
  - **Repositories** handle database queries using SQLAlchemy 2.x.
  This makes the codebase highly modular, easy to navigate, simple to test, and ready to evolve."

### 2. Function-Based vs. Class-Based Code
* **Question**: *Why prefer function-based modules over OOP classes for services and repositories?*
* **Answer**:
  "In Python, wrapping simple procedures in classes without state creates unnecessary boilerplate. Standard functions accepting explicit parameters (like `db: Session`) are simpler, faster, and easier to test. We retain OOP classes strictly for external AI provider abstractions (OCR, LLM, Embeddings) where polymorphism and dynamic provider swapping are beneficial."

### 3. Asynchronous Execution & Direct Storage Upload
* **Question**: *Why does the backend avoid receiving file bytes directly?*
* **Answer**:
  "Handling large file uploads directly in FastAPI blocks server bandwidth and memory. Instead, we issue temporary pre-signed storage URLs. Clients upload directly to Supabase Storage, and our backend performs asynchronous background processing via worker threads (`run_in_threadpool` or async tasks), keeping the API responsive."

### 4. Vector Retrieval & Grounded RAG
* **Question**: *How does your RAG pipeline prevent hallucinations?*
* **Answer**:
  "We generate 1536-dimensional embeddings for OCR document chunks and run `pgvector` cosine similarity searches directly in PostgreSQL. Grounded prompts constrain the LLM to answer using *only* the retrieved context chunks, providing source page citations and returning explicit fallback messages if no context matches."

---

## Future Evolution Roadmap (Background Workers & Microservices)

```text
                  +---------------------------+
                  |  API Gateway / FastAPI    |
                  +-------------+-------------+
                                |
                   (Enqueues Processing Task)
                                |
                                v
                  +---------------------------+
                  |  Message Queue (Redis /   |
                  |     RabbitMQ / Celery)    |
                  +-------------+-------------+
                                |
        +-----------------------+-----------------------+
        |                                               |
        v                                               v
+---------------+---------------+               +---------------+---------------+
|  OCR & Document Worker        |               |  RAG & Vector Retrieval Worker|
|  (Tesseract / AWS Textract)   |               |  (OpenAI / pgvector Worker)   |
+-------------------------------+               +-------------------------------+
```

1. **Celery / RabbitMQ Asynchronous Task Queue**: Offload document processing from FastAPI threadpools to dedicated background workers.
2. **Microservices Decoupling**: Split OCR document extraction into a dedicated worker service, isolating CPU-bound image rendering from vector RAG search.
3. **Redis Caching**: Cache pre-computed chunk embeddings and LLM responses to reduce external API costs and latency.
