# Knowledge Management Platform

An AI-powered knowledge management platform that helps organizations preserve and access institutional knowledge through retrieval-augmented generation (RAG).

## Overview

Institutional knowledge is often distributed across documents, procedures, and employee experience. When experienced employees leave, that knowledge can become difficult to access.

The Knowledge Management Platform provides a conversational interface for asking questions about an organization's knowledge base. The system:

* Authenticates users with JWT-based authentication.
* Stores organizational documents in PostgreSQL.
* Extracts and chunks uploaded `.txt` and `.pdf` documents.
* Generates local 384-dimensional embeddings using FastEmbed and `sentence-transformers/all-MiniLM-L6-v2`.
* Uses PostgreSQL with pgvector for semantic similarity search.
* Applies document authorization during retrieval.
* Uses Google Gemini 3.5 Flash to generate answers from retrieved knowledge.
* Returns supporting source documents with generated answers.
* Reports when requested information is not present in the knowledge base.

## Architecture

```text
Employee
   |
   v
React Frontend
   |
   v
FastAPI Backend
   |
   +--> Authentication / Access Control
   |
   +--> Document Ingestion
   |       |
   |       +--> Text/PDF Extraction
   |       +--> Chunking
   |       +--> FastEmbed / MiniLM
   |       +--> 384-D Embeddings
   |
   +--> Semantic Retrieval
   |       |
   |       +--> PostgreSQL + pgvector
   |       +--> Authorization Filtering
   |
   +--> RAG Prompt Construction
   |       |
   |       v
   |   Google Gemini 3.5 Flash
   |
   v
Grounded Answer + Sources
```

## Technology Stack

### Backend

* Python 3.11
* FastAPI
* SQLAlchemy
* PostgreSQL
* pgvector
* Alembic
* FastEmbed
* `sentence-transformers/all-MiniLM-L6-v2`
* PyPDF
* PyJWT
* pwdlib with Argon2
* Google GenAI SDK

### Frontend

* React 19
* Vite
* React Markdown

### Infrastructure

* PostgreSQL with pgvector
* Docker Compose configuration
* Nginx frontend container
* GitHub Actions CI

## Features

### Authentication

Users authenticate through a username and password. Successful authentication produces a JWT bearer token.

The current access model provides:

* Admin users: access to all documents.
* Regular users: access to documents they own.

Authorization is applied to document access and semantic retrieval.

### Document Ingestion

The application accepts:

* `.txt` files encoded as UTF-8
* `.pdf` files

Uploaded documents are:

1. Extracted into text.
2. Split into chunks.
3. Converted into 384-dimensional embeddings.
4. Stored in PostgreSQL with pgvector.

### Semantic Search

Questions are converted into embeddings and compared with stored document chunks using cosine distance.

The current retrieval threshold is `0.70`, with a default maximum of five returned chunks.

For non-admin users, document ownership filtering is applied before similarity results are returned.

### Retrieval-Augmented Generation

The RAG workflow is:

```text
User Question
     |
     v
Question Embedding
     |
     v
Authorized Semantic Retrieval
     |
     v
Retrieved Knowledge
     |
     v
Prompt Construction
     |
     v
Google Gemini 3.5 Flash
     |
     v
Answer + Supporting Sources
```

The generation prompt instructs the model to use only retrieved knowledge-base content and to report when the available information is insufficient.

## Prerequisites

For local development:

* Python 3.11
* Node.js 20 or later
* npm
* PostgreSQL with the pgvector extension
* Google Gemini API key

Docker Compose configuration is also included for environments where Docker is available.

## Database Setup

The default local database configuration is:

```text
postgresql://kma_user:kma_password@localhost:5432/kma
```

The application reads the database connection string from the `DATABASE_URL` environment variable.

For local development, PostgreSQL must be running with a database and user matching the default configuration, or `DATABASE_URL` must be set to the appropriate connection string.

## Backend Setup

From the repository root:

```bash
cd backend
```

Install the Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Set the required environment variables:

```bash
export DATABASE_URL="postgresql://kma_user:kma_password@localhost:5432/kma"
export JWT_SECRET_KEY="replace-with-a-development-secret"
export GEMINI_API_KEY="your-gemini-api-key"
```

Run the database migrations:

```bash
alembic upgrade head
```

Alternatively, the repository includes a migration helper:

```bash
python run_migrations.py
```

Create an administrator account:

```bash
python create_admin.py
```

Start the FastAPI backend:

```bash
python -m uvicorn app.main:app --reload
```

The backend is available at:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

## Frontend Setup

In a separate terminal:

```bash
cd frontend
npm ci
npm run dev
```

The development frontend is available at:

```text
http://localhost:5173
```

## API Documentation

FastAPI automatically provides interactive API documentation:

```text
http://localhost:8000/docs
```

ReDoc is also available:

```text
http://localhost:8000/redoc
```

### Authentication

```text
POST /auth/token
GET  /auth/me
```

### Documents

```text
POST   /documents/upload
GET    /documents
DELETE /documents/{document_id}
GET    /documents/search
GET    /documents/ask
```

### Health

```text
GET /health
```

Use the interactive `/docs` interface for request parameters, authentication, response schemas, and endpoint testing.

## Optional Test Data

The repository includes a seed script for creating a small known dataset used by integration testing and demonstrations.

From the `backend` directory:

```bash
python scripts/seed_test_data.py
```

The seed dataset includes:

* `vacation_policy.txt`
* `onboarding_checklist.txt`
* `budget_review.txt`

The script also creates a `ci_admin` test administrator account for the seeded test environment.

## Testing

The backend test suite can be run from the `backend` directory:

```bash
pytest -v
```

The current verified baseline is:

```text
48 passed
```

The test suite covers areas including:

* Authentication
* Document upload
* PDF extraction
* Text chunking
* Embedding generation
* Database storage
* Semantic retrieval
* RAG integration
* End-to-end question answering

CI uses a test database and mocks Gemini LLM calls for deterministic testing. Local FastEmbed embeddings are used where applicable.

### Frontend Checks

From the `frontend` directory:

```bash
npm run lint
npm run build
```

## Continuous Integration

GitHub Actions runs automated checks for pushes and pull requests targeting the project's primary branches.

The CI workflow includes:

* Backend dependency installation
* Ruff linting
* Frontend dependency installation
* Frontend build
* Database schema and migration validation
* Document ingestion tests
* Embedding and storage tests
* Semantic retrieval tests
* RAG integration tests
* End-to-end question-answering tests
* Authentication tests

Gemini calls are mocked in CI so automated tests do not depend on an external LLM service.

## Alpha Evaluation Results

The system was evaluated using a ten-question knowledge-base evaluation set and three live AI response-time trials.

| Metric             |               Result |
| ------------------ | -------------------: |
| AI response time   |   ~4 seconds average |
| Retrieval accuracy |         10/10 (100%) |
| Answer support     |         10/10 (100%) |
| Backend tests      | 48/48 passing (100%) |

The retrieval and answer-support results represent this specific ten-question evaluation set and should not be interpreted as a general accuracy guarantee.

## Example Questions

A question supported by the seeded knowledge base:

```text
How many days of paid vacation do employees receive per year?
```

Expected answer:

```text
Employees receive 15 days of paid vacation per year.
```

Supporting source:

```text
vacation_policy.txt
```

A question outside the seeded knowledge base:

```text
What is the company's policy for international business travel?
```

Expected behavior:

```text
The information was not found in the knowledge base.
```

## Docker

The repository includes Dockerfiles for the backend and frontend and a Docker Compose configuration containing:

* PostgreSQL with pgvector
* FastAPI backend
* React/Nginx frontend

The Compose configuration can be started with:

```bash
docker compose up --build
```

The current local development and live-demo workflow was verified outside Docker. The Docker configuration is therefore included as containerized infrastructure, but the live Gemini workflow has not been independently verified inside the Docker environment.

## Project Structure

```text
knowledge-management-platform/
├── .github/
│   └── workflows/
│       └── ci.yml
├── backend/
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   └── services/
│   ├── scripts/
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run_migrations.py
├── frontend/
│   ├── public/
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Current Scope

The current implementation demonstrates the core Alpha workflow:

```text
Authentication
    ↓
Document Access
    ↓
Document Ingestion
    ↓
Semantic Retrieval
    ↓
Authorized Context
    ↓
RAG Generation
    ↓
Grounded Answer + Sources
```

The project is an Alpha/MVP implementation rather than a production deployment. Future development could expand access-control capabilities, knowledge sources, operational monitoring, evaluation coverage, and deployment infrastructure.
