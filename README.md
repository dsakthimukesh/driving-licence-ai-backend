
# AI Document Intelligence – Backend

A FastAPI backend for an AI-powered Driving Licence Document Intelligence application. The system allows users to upload driving licence documents, extract structured information using OCR and LLMs, store document data securely, and ask questions using Retrieval-Augmented Generation (RAG).

## 🚀 Project Links

- **Backend Repository:** https://github.com/dsakthimukesh/driving-licence-ai-backend
- **Frontend Repository:** https://github.com/dsakthimukesh/driving-licence-ai-frontend
- **Live Backend API:** https://driving-licence-ai-backend.onrender.com
- **Interactive API Documentation:** https://driving-licence-ai-backend.onrender.com/docs

## 🌟 Key Features

- User registration and JWT-based authentication
- Secure document upload using Supabase Storage signed URLs
- Driving licence document processing
- OCR-based text extraction using Tesseract
- Structured driving licence information extraction using LLMs
- Gemini LLM with Groq fallback support
- Document metadata and extracted information storage
- Document chunking and vector embeddings
- PostgreSQL vector similarity search using pgvector
- Retrieval-Augmented Generation (RAG) question answering
- Temporary signed download URLs
- Document processing status tracking
- Modular backend architecture

## 🛠️ Technology Stack

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- REST APIs
- JWT authentication
- Docker

### Database and Storage

- Supabase PostgreSQL
- Supabase Storage
- pgvector
- SQLAlchemy ORM

### OCR and AI

- Tesseract OCR
- Google Gemini
- Groq
- Gemini text embeddings
- Retrieval-Augmented Generation (RAG)

### Deployment

- Docker
- Render
- Supabase

## 🏗️ Architecture

The backend follows a modular architecture that separates routing, controllers, business logic, repositories, and database access.

```text
Client
  |
  ▼
FastAPI Routes
  |
  ▼
Controllers
  |
  ▼
Services
  |
  ├── Authentication Service
  ├── Document Service
  ├── Document Processing Service
  ├── LLM Provider
  ├── Embedding Provider
  └── RAG Service
  |
  ▼
Repositories / Database Layer
  |
  ▼
PostgreSQL + Supabase Storage
```

### Main Layers

#### Routes

Defines API endpoints and receives incoming HTTP requests.

#### Controllers

Handles request and response coordination between routes and services.

#### Services

Contains application business logic, document processing, authentication, AI integration, and RAG workflows.

#### Repositories

Handles database operations and separates persistence logic from business logic.

#### Database Layer

Manages database configuration, SQLAlchemy models, and database sessions.

## 📂 Main Processing Flow

```text
Document Upload
      |
      ▼
Generate Signed Upload URL
      |
      ▼
Upload File to Supabase Storage
      |
      ▼
Confirm Upload
      |
      ▼
Start Document Processing
      |
      ▼
Download Document from Storage
      |
      ▼
OCR Text Extraction
      |
      ▼
Structured LLM Extraction
      |
      ▼
Validate Extracted Information
      |
      ▼
Generate Document Chunks
      |
      ▼
Generate Embeddings
      |
      ▼
Store Data and Vectors
      |
      ▼
Mark Processing as Completed
```

## 🤖 AI/LLM Approach

The application uses OCR, LLM-based structured extraction, embeddings, and Retrieval-Augmented Generation.

### OCR

Tesseract OCR is used to extract text from uploaded driving licence documents.

OCR accuracy depends on factors such as:

- Image quality
- Document orientation
- Lighting and contrast
- Text clarity
- Document layout

### Structured Information Extraction

The extracted OCR text is sent to an LLM to identify structured driving licence information.

The extraction process supports fields such as:

- Licence number
- Full name
- Parent name
- Date of birth
- Blood group
- Address
- Issue date
- Expiry date
- Vehicle authorization
- Issuing authority
- Restrictions
- Other information

The response is validated using structured Pydantic models before being stored in the database.

### LLM Provider Strategy

The backend uses a fallback strategy for LLM-based operations.

| Purpose | Provider |
|---|---|
| Primary LLM | Google Gemini |
| Fallback LLM | Groq |
| Embeddings | Google Gemini |

The configured fallback model is:

```text
openai/gpt-oss-120b
```

If the primary Gemini provider encounters supported errors such as quota exhaustion, rate limiting, or certain availability issues, the fallback provider is used.

The fallback mechanism is designed to avoid exposing API keys in logs and to record relevant provider and processing information for troubleshooting.

### Embeddings

Gemini is used to generate document and query embeddings.

- Embedding model: `gemini-embedding-001`
- Vector dimension: `1536`
- Vector storage: PostgreSQL with pgvector

Document text is divided into chunks, and each chunk is converted into a vector embedding before being stored.

## 🔎 Retrieval-Augmented Generation (RAG)

The RAG system allows users to ask questions about a selected document.

### RAG Flow

```text
User Question
      |
      ▼
Generate Query Embedding
      |
      ▼
Search Relevant Document Chunks
      |
      ▼
PostgreSQL + pgvector Similarity Search
      |
      ▼
Build Context from Retrieved Chunks
      |
      ▼
Generate Answer Using LLM
      |
      ▼
Return Answer and Sources
```

### RAG Provider Handling

The RAG service uses the configured LLM provider abstraction. Gemini is used as the primary answer-generation provider, while Groq acts as the fallback provider when supported errors occur.

The embedding process remains separate from LLM answer generation and continues to use Gemini embeddings.

## 🔐 Authentication

The backend implements JWT-based authentication.

### Authentication Flow

1. A user registers using the registration API.
2. The password is securely hashed before storage.
3. The user logs in using their credentials.
4. The backend validates the credentials.
5. The backend generates a JWT access token.
6. The frontend sends the token in the `Authorization` header.
7. Protected endpoints validate the token before processing the request.

Example authorization header:

```http
Authorization: Bearer <access_token>
```

The application uses a custom users table rather than relying on Supabase Auth.

## 📦 Storage and Signed URLs

The application uses a private Supabase Storage bucket for uploaded documents.

The backend generates temporary signed URLs for file operations.

### Upload Process

1. The client requests an upload URL.
2. The backend validates the request.
3. The backend generates a signed Supabase Storage URL.
4. The client uploads the file directly to Supabase Storage.
5. The client confirms the upload with the backend.

This approach avoids sending the complete file through the backend and prevents exposing Supabase service credentials to the frontend.

## 🗄️ Database

The application uses PostgreSQL through Supabase.

The database includes tables for:

- Users
- Documents
- Document information
- Document chunks

The document chunks table stores vector embeddings used for similarity search.

### Vector Search

pgvector is used to retrieve document chunks that are semantically relevant to the user's question.

The retrieved chunks are then supplied as context to the LLM for answer generation.

## 📁 Project Structure

```text
app/
├── api/
│   └── v1/
│       ├── auth/
│       └── documents/
├── core/
│   ├── config.py
│   └── security.py
├── database/
│   ├── models/
│   ├── repositories/
│   └── session.py
├── schemas/
├── services/
│   ├── llm/
│   │   ├── provider.py
│   │   └── init.py
│   ├── document_processing_service.py
│   ├── rag_service.py
│   └── ...
├── controllers/
├── repositories/
└── main.py

tests/
```

The exact structure may vary depending on the latest repository implementation.

## ⚙️ Local Setup

### Prerequisites

- Python 3.10 or later
- PostgreSQL/Supabase project
- Supabase Storage bucket
- Gemini API key
- Groq API key
- Tesseract OCR
- Git
- Docker (optional)

### Clone the Repository

```bash
git clone https://github.com/dsakthimukesh/driving-licence-ai-backend.git
cd driving-licence-ai-backend
```

### Create a Virtual Environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file using `.env.example` as a reference.

The configuration requires values for the database, Supabase, authentication, AI providers, and OCR.

Example configuration:

```env
DATABASE_URL=<your_database_url>

SUPABASE_URL=<your_supabase_url>
SUPABASE_SERVICE_KEY=<your_supabase_service_key>

GEMINI_API_KEY=<your_gemini_api_key>
GEMINI_GENERATION_MODEL=gemini-3.6-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001

GROQ_API_KEY=<your_groq_api_key>
GROQ_MODEL=openai/gpt-oss-120b

JWT_SECRET_KEY=<your_jwt_secret>
CORS_ORIGINS=http://localhost:5173

TESSERACT_CMD=<path_to_tesseract>
```

**Security:** Never commit `.env` files, API keys, database credentials, service keys, or JWT secrets to the repository.

### Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

## 🐳 Docker

The backend includes Docker deployment configuration.

Build the Docker image:

```bash
docker build -t driving-licence-ai-backend .
```

Run the container:

```bash
docker run --env-file .env -p 8000:8000 driving-licence-ai-backend
```

For cloud deployment, the application uses the port provided by the hosting platform.

## ☁️ Deployment

The backend is deployed on Render using Docker.

### Deployment Configuration

- Service: Render Web Service
- Deployment method: Docker
- Database: Supabase PostgreSQL
- Storage: Supabase Storage
- Environment configuration: Render environment variables

The application binds to the host and port configured by the deployment environment.

### Production Configuration

Production environment variables should be configured directly in Render.

The frontend uses the deployed backend URL:

```text
https://driving-licence-ai-backend.onrender.com
```

CORS configuration should include the deployed frontend origin.

## 🔑 Key Technical Decisions

### Signed URL File Uploads

Temporary signed URLs allow the frontend to upload documents directly to private storage without exposing service credentials.

### Modular Backend Architecture

Routes, controllers, services, and repositories are separated to improve maintainability, testing, and future extension.

### Provider Abstraction

The LLM provider abstraction allows different LLM providers to be used without tightly coupling business logic to a single provider.

### Gemini and Groq Fallback

The fallback provider improves resilience when the primary LLM provider encounters quota or availability issues.

### Separate Embedding Provider

Embedding generation is handled separately from text generation because document and query vectors must remain compatible with the configured vector database dimensions.

### PostgreSQL and pgvector

PostgreSQL with pgvector provides a unified storage solution for application data, document chunks, and vector similarity search.

### Structured Validation

Pydantic validation helps ensure that LLM-generated extraction results conform to the expected response structure before database persistence.

## ⚠️ Known Limitations

- OCR results depend on the quality and format of the uploaded document.
- LLM-generated extraction may contain incorrect or incomplete information.
- Extracted information should be reviewed against the original document.
- Gemini and Groq API usage is subject to provider quotas and availability.
- The current application focuses on driving licence documents.
- The system has not been validated through large-scale load testing.
- The application has not undergone a formal security audit.
- LLM fallback does not eliminate provider rate limits or service outages.
- Local OCR setup requires Tesseract to be installed and configured correctly.

## 🧰 AI Development Tools Used

### Antigravity

Antigravity was used as an AI-assisted development tool for:

- Supporting backend implementation
- Improving service and provider integration
- Assisting with debugging
- Updating test cases
- Reviewing implementation changes

AI-assisted development was combined with manual testing, API testing, deployment verification, and end-to-end application testing.

### AI Providers

- Google Gemini for structured extraction and embeddings
- Groq for fallback LLM-based processing

## 🧪 Testing and Validation

The backend was tested through the application flow, including:

1. User registration
2. User login
3. Signed upload URL generation
4. Document upload confirmation
5. Document processing
6. OCR extraction
7. Structured information extraction
8. Database persistence
9. Vector embedding generation
10. RAG question answering
11. Gemini-to-Groq fallback behavior
12. Deployed API health verification

Automated tests were also used during development to validate backend functionality and LLM provider behavior.

## 🔗 API Documentation

When the backend is running, interactive API documentation is available through FastAPI Swagger UI:

```text
/docs
```

OpenAPI JSON:

```text
/openapi.json
```

The deployed API documentation is available at:

https://driving-licence-ai-backend.onrender.com/docs

## 📌 Future Improvements

- Support additional identity and government document formats
- Improve OCR preprocessing and accuracy
- Add confidence scores for extracted fields
- Add asynchronous background job processing using a dedicated queue
- Improve observability and monitoring
- Add more comprehensive integration tests
- Add stronger document validation
- Support configurable LLM provider routing
- Improve production authentication and security controls

## 👨‍💻 Author

**Sakthi**

GitHub: https://github.com/dsakthimukesh