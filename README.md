# Voda EHRs

Voda EHRs is my final-year software development project. It is a web-based electronic health records system designed to explore how patient information can be stored and accessed more securely.

The project includes normal EHR functions such as patient profiles, medical records, and uploaded documents. Its main focus is access control: a user should only be able to view or change information when their role, permissions, and the patient's consent allow it.




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

Install the packages, apply the database migrations, seed the development data, and run FastAPI:

```bash
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

Run the migration and seed commands from the `backend` directory after the PostgreSQL and MinIO services are running. `alembic upgrade head` brings the database schema to the latest version; `python -m app.seed` creates the development roles, admin account, sample clinicians, patients, records, documents, and appointments. Use the seed command for a new local database; it updates existing core accounts but may add development sample documents when repeated.

The backend reads its configuration from the root `.env` file created in step 1. Ensure it includes the database, MinIO, security-key, and initial-admin settings before running these commands. Development credentials, including the seeded sample accounts, are for local use only.



### 3. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend is available at http://localhost:5173.

## Current API routes

| Method | Route | Current purpose |
|--------|-------|-----------------|
| GET | `/api/v1/health` | Confirms that the backend is running |
| GET | `/api/v1/auth/status` | Temporary authentication-module status route |
| GET | `/api/v1/users/me` | Demonstrates a protected-route pattern |



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



## Development roadmap

1. Complete user accounts, login, and role management.
2. Add patient profiles and permission checks.
3. Add medical records and encrypted document storage.
4. Implement consent controls, audit review, and record versioning.
5. Add emergency access, testing, and final security review.

## Project status

Voda EHRs is my final-year project. I will update this README as I build and test each feature.
