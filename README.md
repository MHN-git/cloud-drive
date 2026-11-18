# Personal Cloud Drive

A personal cloud storage service built with Django REST Framework, MinIO, Kafka, Redis, PostgreSQL, and Nginx.

The project provides a simple file management system where users can create folders, upload and download files, and manage their storage quota.

## Features

- JWT-based authentication and user registration
- User-owned folders and files
- Direct file uploads to MinIO using presigned URLs
- Direct file downloads using presigned URLs
- Asynchronous upload completion using Kafka consumers
- Storage quota management
- Redis caching for quota information and folder file lists
- PostgreSQL for persistent metadata storage
- Nginx as a reverse proxy for API and object storage traffic
- Docker Compose-based service orchestration
- OpenAPI documentation with Swagger UI
- Health and readiness endpoints

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Programming language |
| Django 5.2 | Backend framework |
| Django REST Framework | REST API |
| Simple JWT | Authentication |
| PostgreSQL 17 | Relational database |
| MinIO | Object storage |
| Apache Kafka 4.1.1 | Event messaging |
| Redis 8 | Caching |
| Nginx | Reverse proxy |
| Docker Compose | Service orchestration |
| drf-spectacular | OpenAPI documentation |

## Architecture Overview

The application consists of the following services:

- **API:** Handles authentication, file and folder management, and presigned URL generation.
- **PostgreSQL:** Stores users, file metadata, folder metadata, and quota information.
- **MinIO:** Stores uploaded file objects.
- **Kafka:** Handles asynchronous upload completion and quota recalculation events.
- **Consumers:** Process Kafka events independently of the API.
- **Redis:** Caches quota information and folder file lists.
- **Nginx:** Routes API requests to Django and object storage requests to MinIO.

See [ARCHITECTURE.md](ARCHITECTURE.md) for more details.

## Prerequisites

Make sure the following tools are installed:

- Docker
- Docker Compose

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/MHN-git/cloud-drive.git
cd cloud-drive
```

### 2. Configure environment variables

Create your environment file from the example:

```bash
cp .env.example .env
```

On Windows CMD:

```cmd
copy .env.example .env
```

Fill in the required values in `.env`.

Example configuration for Docker Compose:

```env
SECRET_KEY=replace-with-a-secure-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=cloud_drive
DB_USER=postgres
DB_PASSWORD=replace-with-a-secure-password
DB_HOST=postgres
DB_PORT=5432

MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=replace-with-a-secure-password

MINIO_ENDPOINT=minio:9000
MINIO_PUBLIC_ENDPOINT=localhost:8080
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=replace-with-a-secure-password

MINIO_BUCKET=cloud-drive
MINIO_SECURE=False
MINIO_PRESIGNED_URL_EXPIRY_SECONDS=600

KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_UPLOAD_COMPLETED_TOPIC=file.upload.completed
KAFKA_QUOTA_RECALCULATE_TOPIC=quota.recalculate

REDIS_URL=redis://redis:6379/1

DEFAULT_QUOTA_MB=100
```

Use matching MinIO credentials for `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` and `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` when using the default MinIO root account.

Use your own secure credentials instead of the example values.

### 3. Start the application

Build the images and start all services:

```bash
docker compose up --build -d
```

Check the running containers:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f
```

## Service Endpoints

| Service | URL |
|---|---|
| API through Nginx | http://localhost:8080 |
| Swagger UI | http://localhost:8080/api/docs/ |
| OpenAPI Schema | http://localhost:8080/api/schema/ |
| Liveness Check | http://localhost:8080/api/health/live/ |
| Readiness Check | http://localhost:8080/api/health/ready/ |
| MinIO Console | http://localhost:9001 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| Kafka external listener | localhost:9094 |

## API Overview

API endpoints are versioned under `/api/v1/`.

### Authentication

- `POST /api/v1/auth/signup/` — Register a new user.
- `POST /api/v1/auth/token/` — Obtain JWT access and refresh tokens.
- `POST /api/v1/auth/token/refresh/` — Refresh an access token.
- `GET /api/v1/auth/me/quota` — Retrieve the authenticated user's quota information.

### Folders

Folder management endpoints are available under:

```text
/api/v1/folders/
```

### Files

File management endpoints are available under:

```text
/api/v1/files/
```

The file API also provides actions for generating upload URLs, completing uploads, and generating download URLs.

For detailed request and response schemas, open Swagger UI.

## Upload Workflow

1. The client requests file creation through the API.
2. Django validates the request and reserves the required quota.
3. Django creates a pending file record and returns the file information.
4. The client requests a presigned upload URL.
5. The client uploads the file directly to MinIO through Nginx.
6. The client calls the complete-upload endpoint.
7. Django publishes an upload completion event to Kafka.
8. The upload consumer verifies the object in MinIO and updates the file status.
9. A quota recalculation event is published and processed by the quota consumer.

## Download Workflow

1. The client requests a download URL for a file.
2. Django verifies file ownership and readiness.
3. Django generates a presigned download URL.
4. The client downloads the file directly from MinIO through Nginx.

File contents are not transferred through Django.

## Stopping the Application

Stop the containers:

```bash
docker compose down
```

To remove persistent volumes as well:

```bash
docker compose down -v
```

**Warning:** The second command deletes persistent database, MinIO, Kafka, and Redis data.

## License

This project was developed as a personal backend engineering project.

