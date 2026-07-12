# Voda EHRs

Voda EHRs is my final-year software development project. It is a web-based electronic health records system designed to explore how patient information can be stored and accessed more securely.

The project includes normal EHR functions such as patient profiles, medical records, and uploaded documents. Its main focus is access control: a user should only be able to view or change information when their role, permissions, and the patient's consent allow it.

Current stage: The project foundation is working. The main healthcare and security workflows are still under development.

## Current progress

The following parts are currently working:

- React and TypeScript frontend created with Vite
- Login screen interface and dashboard layout
- Light and dark theme support
- FastAPI backend with versioned API routes
- Frontend connection to the backend health endpoint
- PostgreSQL and MinIO running through Docker Compose
- Environment variable templates for local development
- Basic application, security, and audit log separation

Some security utilities have also been started, but they are not yet connected to a complete login or patient-record workflow:

- Argon2id password hashing utility
- JWT creation and validation utility
- Example protected backend route
- Database and MinIO client configuration
- Basic security response headers

## Planned features

The completed system is intended to support:

- Secure user authentication
- Role-based access for administrators, doctors, nurses, receptionists, patients, and auditors
- Patient profile and medical record management
- Patient consent controls
- Encryption of medical records and uploaded files
- Record version history and digital signatures
- Audit logging for security-relevant actions
- Controlled emergency access with a recorded reason

These features will be added and tested in stages. They should not be considered complete in the current version.

## Technologies

| Area | Technology |
|------|------------|
| Frontend | React, TypeScript, Vite, and Tailwind CSS |
| Backend | FastAPI and Python |
| Database | PostgreSQL |
| File storage | MinIO |
| Infrastructure | Docker and Docker Compose |
| Security | Argon2id, JWT, and the Python Cryptography library |

## Project structure

```text
.
├── backend/              # FastAPI application
├── frontend/             # React application
├── docker-compose.yml    # PostgreSQL and MinIO services
├── .env.example          # Root environment template
└── README.md
```

## Running the project locally

### Requirements

- Python 3.11 or later
- Node.js 18 or later
- Docker Desktop
- Git

### 1. Start PostgreSQL and MinIO

From the project root:

```bash
cp .env.example .env
docker compose up -d
```

### 2. Start the backend

```bash
cd backend
python -m venv .venv
```

Activate the environment on macOS or Linux:

```bash
source .venv/bin/activate
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the packages and run FastAPI:

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

The API documentation is available at http://localhost:8000/docs.

### 3. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The frontend is available at http://localhost:5173.

## Current API routes

| Method | Route | Current purpose |
|--------|-------|-----------------|
| GET | `/api/v1/health` | Confirms that the backend is running |
| GET | `/api/v1/auth/status` | Temporary authentication-module status route |
| GET | `/api/v1/users/me` | Demonstrates a protected-route pattern |

The authentication and user routes are placeholders and will change as the database-backed login system is implemented.

## Development checks

Frontend:

```bash
npm run lint
npm run build
```

Backend:

```bash
ruff check app alembic
black --check app alembic
isort --check-only app alembic
```

## Data and security note

No real patient information should be added to this repository. Development and testing will use fictional sample data created for the project.

Files containing passwords, keys, or local environment settings must remain outside Git. Only `.env.example` files should be committed.

## Development roadmap

1. Complete user accounts, login, and role management.
2. Add patient profiles and permission checks.
3. Add medical records and encrypted document storage.
4. Implement consent controls, audit review, and record versioning.
5. Add emergency access, testing, and final security review.

## Project status

Voda EHRs is my final-year project. I will update this README as I build and test each feature.
