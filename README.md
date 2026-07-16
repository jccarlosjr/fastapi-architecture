# FastAPI Minimal Architecture (fast-api-min)

[Versão em Português (README_PT.md)](README_PT.md)

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.139.0-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D31D24?style=flat-square&logo=sqlite&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=flat-square&logo=docker&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-Passed-0A9EDC?style=flat-square&logo=pytest&logoColor=white)

An extremely robust, highly abstracted, and fully object-oriented (Class-Based) backend architecture built on top of **FastAPI**, **SQLAlchemy (Async)**, **PostgreSQL**, and **Redis**.

The project eliminates common FastAPI boilerplate through a flexible generic layer for CRUDs, automated exception handling, dynamic Pydantic schemas, granular role-based access control (RBAC), and enterprise-grade security.

---

## Core Technologies

- **Core**: Python 3.11, FastAPI.
- **Database**: PostgreSQL (SQLAlchemy 2.0 Async Engine) & Alembic for migrations.
- **Cache & Rate-Limit**: Redis.
- **Security**: JWT Auth with opaque refresh token rotation saved in Redis, Progressive Backoff against brute-force logins, and OWASP Security Headers.
- **Environment**: Docker & Docker Compose.

---

## Directory Structure

```bash
├── app/
│   ├── api/                  # Main router and version manager
│   ├── core/
│   │   ├── generics/         # Base abstractions: Models, Repositories, Services, and Views
│   │   ├── config.py         # Global settings (Pydantic Settings)
│   │   ├── exceptions.py     # Object-oriented exception handling
│   │   ├── middlewares.py    # Request logs, OWASP headers, and rate limiters
│   │   ├── mixins.py         # Security mixins (LoginRequired, StaffRequired, etc.)
│   │   └── security.py       # Cryptographic utilities and token generation
│   ├── db/                   # Session initialization and async pool (SQLAlchemy / Redis)
│   └── modules/              # Domain modules (Isolated business rules)
│       ├── accounts/         # User registration and updates
│       ├── auth/             # Login, logout, and token rotation
│       ├── groups/           # Access profiles/Groups
│       └── permissions/      # System permissions (RBAC)
```

---

## Getting Started

### Prerequisites
- Docker & Docker Compose installed.

### Steps to run:

1. **Configure Environment Variables**:
   Create a `.env` file based on the [.env.example](.env.example) template:
   ```env
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=app_db
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app_db
   REDIS_URL=redis://redis:6379/0
   SECRET_KEY=your_super_secure_secret_key
   ```

2. **Spin Up the Containers**:
   Execute Docker Compose to build images, create databases, and start the Uvicorn server:
   ```bash
   docker compose up -d --build
   ```

3. **Initialize the Database (Management CLI)**:
   Since the database starts empty and access is protected by RBAC, you must seed default permissions and create the first administrator user interactively:
   ```bash
   # Seed default CRUD permissions for domain models
   docker compose exec web python cli.py seed-permissions

   # Create the first superuser interactively
   docker compose exec web python cli.py createsuperuser
   ```

4. **Verify Container Logs**:
   ```bash
   docker compose logs -f web
   ```

5. **Access the API**:
   - API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
   - Diagnostic Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Running Automated Tests

You can execute the test suite using `pytest` directly inside the web container:
```bash
docker compose exec web env PYTHONPATH=. pytest
```

---

## Complete Documentation

For an in-depth analysis of the project's architecture, object-oriented patterns, generic views, role-based access control, and security details, please check:

[DOCUMENTATION.md](DOCUMENTATION.md)
