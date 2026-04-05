# Zorvyn Finance API

A role-based financial records management backend built with **FastAPI** + **SQLAlchemy 2.0 (async)** + **PostgreSQL**, fully containerised with **Docker Compose**.

Designed following **Clean Architecture** (layered separation), **DRY**, **high cohesion / low coupling** principles.

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/krishhsuri/Zorvyn
cd Zorvyn

# 2. Copy environment config
cp .env.example .env
# Edit SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD as needed

# 3. Start everything with Docker
docker compose up --build
```

A default **admin account** is seeded automatically on first startup:
- Email: `admin@zorvyn.com`
- Password: `admin123`



### Seed Demo Data

```bash
docker compose exec app python -m scripts.seed
```

This creates demo analyst/viewer users and ~60 realistic financial records.

---

## Architecture

```
Request
  │
  ▼
┌──────────────────────────────┐
│  API Layer  (app/api/v1/)    │  Routes only — thin controllers
│  FastAPI routers + Pydantic  │  No business logic here
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Service Layer               │  Business rules, validation,
│  (app/services/)             │  aggregation, orchestration
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Repository Layer            │  DB queries only
│  (app/repositories/)        │  SQLAlchemy async
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Infrastructure              │
│  (app/core/, app/models/)   │ Config, DB engine, ORM models
└──────────────────────────────┘
```

**Key principle:** Routes call Services → Services call Repositories → Repositories call the DB. Business rules never cross layer boundaries.

---

## Tech Stack

| Component | Technology |
|---|---|
| Framework | FastAPI 0.115 |
| Language | Python 3.12 |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Async Driver | asyncpg |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt |
| Validation | Pydantic v2 |
| Testing | pytest + httpx + aiosqlite |
| Containerisation | Docker + Docker Compose |

---

## Role Model

Permissions are attached to roles, never directly to users.

| Permission | Viewer | Analyst | Admin |
|---|:---:|:---:|:---:|
| View own records | ✓ | ✓ | ✓ |
| View all records | ✗ | ✗ | ✓ |
| Filter records | ✓ | ✓ | ✓ |
| Create records | ✗ | ✗ | ✓ |
| Update records | ✗ | ✗ | ✓ |
| Delete records | ✗ | ✗ | ✓ |
| View summary | ✓ | ✓ | ✓ |
| Category breakdown | ✗ | ✓ | ✓ |
| Trends analytics | ✗ | ✓ | ✓ |
| Recent activity | ✓ | ✓ | ✓ |
| Export CSV/JSON | ✗ | ✓ | ✓ |
| Manage users | ✗ | ✗ | ✓ |

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/login` | Email + password → JWT tokens |
| POST | `/api/v1/auth/refresh` | Refresh token → new token pair |

### Users (Admin only)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/users/` | Create user |
| GET | `/api/v1/users/` | List users (paginated) |
| GET | `/api/v1/users/{id}` | Get user details |
| PATCH | `/api/v1/users/{id}` | Update user |
| PATCH | `/api/v1/users/{id}/deactivate` | Soft-deactivate user |

### Financial Records

| Method | Endpoint | Roles | Description |
|---|---|---|---|
| POST | `/api/v1/records/` | Admin | Create record |
| GET | `/api/v1/records/` | All | List + filter + paginate |
| GET | `/api/v1/records/export` | Analyst, Admin | Export as CSV or JSON |
| GET | `/api/v1/records/{id}` | All | Get single record |
| PUT | `/api/v1/records/{id}` | Admin | Update record |
| DELETE | `/api/v1/records/{id}` | Admin | Soft-delete record |

**Query Parameters for listing:**

| Parameter | Type | Description |
|---|---|---|
| `type` | `income` / `expense` | Filter by record type |
| `category` | string | Filter by category |
| `date_from` | YYYY-MM-DD | Start date |
| `date_to` | YYYY-MM-DD | End date |
| `search` | string | Search in description/category |
| `page` | int (≥1) | Page number |
| `limit` | int (1–100) | Results per page |

### Dashboard & Analytics

| Method | Endpoint | Roles | Description |
|---|---|---|---|
| GET | `/api/v1/dashboard/summary` | All | Total income, expenses, balance |
| GET | `/api/v1/dashboard/by-category` | Analyst, Admin | Category-wise breakdown |
| GET | `/api/v1/dashboard/trends` | Analyst, Admin | Monthly/weekly time-series |
| GET | `/api/v1/dashboard/recent` | All | Recent N records |

---



---

## Running Tests

Tests use an in-memory SQLite database for speed — no Docker required.

```bash
# Install dependencies locally
pip install -r requirements.txt

# Run all tests
pytest -v

# Run with coverage
pip install pytest-cov
pytest --cov=app --cov-report=term-missing

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v
```

Or inside Docker:

```bash
docker compose exec app pytest -v
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async database connection string |
| `SECRET_KEY` | `change-me` | JWT signing secret |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | `10080` | Refresh token TTL (7 days) |
| `ADMIN_EMAIL` | `admin@zorvyn.com` | Auto-seeded admin email |
| `ADMIN_PASSWORD` | `admin123` | Auto-seeded admin password |

---

## Design Decisions & Assumptions

1. **PostgreSQL** for persistence — production-grade relational DB. Swap `DATABASE_URL` to any async-compatible driver for different databases.

2. **Numeric(12, 2)** for monetary amounts — financial data must never use floating-point due to IEEE 754 rounding errors.

3. **Soft delete** — records are flagged `is_deleted=True` rather than permanently removed. This preserves audit trails, consistent with financial data best practices.

4. **Category normalised to lowercase** — ensures consistent grouping in analytics regardless of input casing.

5. **Admin auto-seed on startup** — avoids bootstrapping problems. The default admin is created if none exists.

6. **Service layer between routes and repositories** — business logic (validation, ownership checks, aggregation) is isolated from both HTTP concerns and database details.

7. **UUID primary keys** — avoids sequential ID enumeration attacks, suitable for distributed systems.

8. **JWT with access + refresh token pattern** — access token is short-lived (30 min), refresh token enables seamless re-authentication without re-entering credentials.

---

## Optional Enhancements Included

- ✅ JWT Authentication (access + refresh tokens)
- ✅ Pagination for all list endpoints
- ✅ Search functionality (description + category)
- ✅ Unit + Integration tests
- ✅ Auto-generated API documentation (Swagger + ReDoc)
- ✅ CSV and JSON export
- ✅ Docker Compose setup
- ✅ Demo data seeder
- ✅ Role-based access control (RBAC)
- ✅ Soft-delete for audit trails

---

## AI-Assisted Development

This project was built with the assistance of **Claude (Anthropic)** via **Gemini Antigravity**, an agentic AI coding assistant. The AI was used as a pair-programming partner — not as a black-box code generator. Every architectural decision, design pattern, and implementation detail was reviewed, understood, and validated before inclusion.

### How AI Was Used

| Phase | AI Contribution | Human Contribution |
|---|---|---|
| **Planning** | Generated implementation plan with architecture options | Chose FastAPI + PostgreSQL + Docker, set design principles (DRY, high cohesion/low coupling) |
| **Scaffolding** | Created project structure and file skeletons | Reviewed structure, approved layered architecture |
| **Implementation** | Wrote initial code for all layers | Reviewed business logic, validated role matrix, verified SQL aggregations |
| **Testing** | Generated unit + integration test suites | Defined test scenarios, verified coverage of edge cases |
| **Documentation** | Drafted README sections | Refined wording, added design rationale |

### Why Disclose AI Usage

Transparency matters. AI is a tool — like a linter, a framework, or Stack Overflow. What matters is whether the developer **understands** the code, can **debug** it, can **extend** it, and can **explain** every decision. This README and the codebase itself demonstrate that understanding.

---

## Structured Prompts Used

Below are representative prompts that were used during development to guide the AI assistant. These illustrate the thought process behind the project's architecture and implementation.

### Prompt 1 — Initial Architecture & Tech Stack
```
Build a Python-based finance tracking system backend.
Use FastAPI and PostgreSQL, containerised with Docker Compose.
Follow Clean Architecture — separate API routes, services (business logic),
repositories (DB queries), and infrastructure (config, ORM).
Apply high cohesion, low coupling, and DRY principles throughout.
Include JWT auth with role-based access (viewer, analyst, admin).
```

### Prompt 2 — Data Model Design
```
Design the ORM models for a finance system:
- User model: UUID PK, email (unique), hashed_password, full_name,
  role (enum: viewer/analyst/admin), is_active (soft delete), timestamps.
- FinancialRecord model: UUID PK, FK to user, amount (Numeric 12,2 — never float),
  type (income/expense), category (normalised lowercase), date, description,
  is_deleted (soft delete), timestamps.
Use SQLAlchemy 2.0 mapped_column style.
```

### Prompt 3 — Service Layer with Business Rules
```
Create the record service layer with these rules:
- Category must be normalised to lowercase on create/update.
- Amount must be positive (enforced at schema level with Pydantic).
- Viewers and Analysts can only see their own records.
- Admins can see and manage all records.
- Deletes are soft — set is_deleted=True, never remove rows.
- Include ownership checks before any mutation.
Keep all business logic here, not in routes or repositories.
```

### Prompt 4 — Analytics Aggregations
```
Build SQL aggregation queries for the dashboard:
1. Summary: total income, total expenses, balance, record count
   — use CASE WHEN inside SUM for type-conditional aggregation.
2. Category breakdown: group by category, with total, count, and percentage.
3. Trends: income/expense grouped by month (YYYY-MM) or ISO week (YYYY-WNN)
   — use PostgreSQL to_char for period formatting.
4. Recent activity: last N records ordered by date desc.
All queries must exclude soft-deleted records and scope by user role.
```

### Prompt 5 — Test Strategy
```
Write tests using pytest + httpx AsyncClient against an in-memory SQLite DB:
- Unit tests: JWT creation/decode, password hashing, service-layer logic
  (duplicate email check, category normalisation, role-based scoping).
- Integration tests: Full endpoint tests for auth (login, refresh, invalid creds),
  records (CRUD, filters, pagination, RBAC), and dashboard (summary, breakdown,
  trends with role restrictions).
Use fixtures for test users, tokens, and sample records.
```

### Prompt 6 — Debugging Docker + Async Issues
```
The app uses asyncpg for PostgreSQL and aiosqlite for tests.
Common issues to handle:
- Docker: app starts before DB is ready → use depends_on + healthcheck.
- Alembic: needs async engine config → use async_engine_from_config.
- Tests: SQLite doesn't support to_char → tests skip PG-specific aggregations.
- Sessions: commits in DI dependency, not in routes → use try/commit/rollback pattern.
```

---

## Debugging Guide

### Common Issues & Solutions

#### 1. `docker compose up` — app crashes with "Connection refused"

**Cause:** The app container starts before PostgreSQL finishes initialising.

**Fix:** The `docker-compose.yml` already includes a health check. If still failing:
```bash
# Restart with a clean build
docker compose down -v
docker compose up --build
```

#### 2. `ModuleNotFoundError: No module named 'app'`

**Cause:** Running from the wrong directory or missing the project root in `PYTHONPATH`.

**Fix:**
```bash
# Always run from the project root
cd d:\Zorvyn

# If running outside Docker, ensure you're in a venv with deps installed
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run the server from project root
uvicorn app.main:app --reload
```

#### 3. `sqlalchemy.exc.OperationalError: could not connect to server`

**Cause:** `DATABASE_URL` in `.env` points to `db:5432` (Docker hostname) but you're running locally.

**Fix:** Update `.env` for local development:
```env
# Local PostgreSQL
DATABASE_URL=postgresql+asyncpg://zorvyn:zorvyn_pass@localhost:5432/zorvyn_finance
```

#### 4. Tests fail with `no such function: to_char`

**Cause:** `to_char()` is a PostgreSQL-specific function. The test suite uses in-memory SQLite which doesn't support it.

**Fix:** The trends endpoint tests may produce empty results on SQLite — this is expected. For full integration testing, use the Docker setup:
```bash
docker compose exec app pytest tests/integration/ -v
```

#### 5. `401 Unauthorized` on all endpoints

**Cause:** Missing or expired JWT token.

**Fix:**
```bash
# 1. Login to get tokens
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@zorvyn.com", "password": "admin123"}'

# 2. Use the access_token in subsequent requests
curl http://localhost:8000/api/v1/records/ \
  -H "Authorization: Bearer <access_token_here>"

# 3. If expired, refresh it
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token_here>"}'
```

#### 6. `422 Unprocessable Entity` on record creation

**Cause:** Pydantic validation failed — check the `errors` array in the response.

**Common mistakes:**
```json
// ❌ Wrong — amount must be positive
{"amount": "-50.00", "type": "expense", "category": "food", "date": "2026-03-15"}

// ❌ Wrong — type must be "income" or "expense"
{"amount": "50.00", "type": "debit", "category": "food", "date": "2026-03-15"}

// ✅ Correct
{"amount": "50.00", "type": "expense", "category": "food", "date": "2026-03-15"}
```

#### 7. `bcrypt` installation errors on Windows

**Cause:** `bcrypt` needs a C compiler on some systems.

**Fix:**
```bash
# Install pre-built wheel
pip install bcrypt --only-binary :all:

# Or use Docker (avoids all native dependency issues)
docker compose up --build
```

#### 8. How to reset the database

```bash
# Docker — delete the volume and rebuild
docker compose down -v
docker compose up --build

# Then re-seed demo data
docker compose exec app python -m scripts.seed
```

#### 9. How to check what's in the database

```bash
# Connect to PostgreSQL inside Docker
docker compose exec db psql -U zorvyn -d zorvyn_finance

# Useful queries
SELECT * FROM users;
SELECT COUNT(*), type FROM financial_records WHERE is_deleted = false GROUP BY type;
SELECT category, SUM(amount) FROM financial_records GROUP BY category ORDER BY SUM(amount) DESC;
```
