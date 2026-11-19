# Personal Cloud Drive

A personal cloud storage service built with Django REST Framework, MinIO, Kafka, Redis, PostgreSQL, and Nginx.

The application allows users to register, authenticate, manage folders and files, upload and download files directly through MinIO, and manage their storage quota.

## Features

- JWT-based authentication
- User-owned folders and files
- Direct file uploads to MinIO using presigned URLs
- Direct file downloads using presigned URLs
- Asynchronous upload completion using Kafka consumers
- Storage quota reservation and recalculation
- Redis caching for quota information and folder file lists
- PostgreSQL for persistent metadata
- Nginx reverse proxy for API and object storage traffic
- Docker Compose-based deployment
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

- **API:** Handles authentication, file and folder management, quota validation, and presigned URL generation.
- **PostgreSQL:** Stores users, folders, files, and quota information.
- **MinIO:** Stores uploaded file objects.
- **Kafka:** Handles asynchronous upload completion and quota recalculation events.
- **Consumers:** Process Kafka events independently of the API.
- **Redis:** Caches quota information and folder file lists.
- **Nginx:** Routes API requests to Django and object storage requests to MinIO.

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture and data flow.

## Prerequisites

- Docker
- Docker Compose

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/MHN-git/cloud-drive.git
cd cloud-drive
```

### 2. Configure environment variables

Create the environment file:

```bash
cp .env.example .env
```

On Windows CMD:

```cmd
copy .env.example .env
```

Configure the values in `.env`.

Example Docker Compose configuration:

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

Use matching MinIO credentials for the root account and the application credentials when using the default MinIO root user.

Replace example passwords and secret keys with secure values.

### 3. Start the application

Build and start all services:

```bash
docker compose up --build -d
```

Check service status:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f
```

Database migrations are applied automatically by the `migrate` service before the API starts.

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

## API Usage

All API endpoints are available under `/api/v1/`.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/signup/` | Register a user |
| POST | `/api/v1/auth/token/` | Obtain JWT tokens |
| POST | `/api/v1/auth/token/refresh/` | Refresh access token |
| GET | `/api/v1/auth/me/quota` | Retrieve user