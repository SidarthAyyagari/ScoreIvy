# ScoreIvy

An exam platform for creating, taking, and grading multiple-choice tests.

## Project Structure

```
ScoreIvy/
├── frontend/          # Next.js React frontend application
├── backend/           # FastAPI Python backend service
└── database/          # PostgreSQL database initialization scripts
```

## Quick Start

**Start everything with one command:**
```bash
./start.sh
```

This will start:
- 🗄️  Database (Docker/PostgreSQL) on port 5432
- 🔧 Backend (FastAPI) on `http://localhost:8000`
- 🎨 Frontend (Next.js) on `http://localhost:3000`

**Stop everything:**
```bash
./stop.sh
```

Or press `Ctrl+C` in the terminal where `start.sh` is running.

## Getting Started (Manual)

### Quick Start Script (Recommended)

```bash
./start.sh
```

### Manual Setup

#### Database

Start with Docker:
```bash
docker-compose up -d
```

Or see `database/README.md` for manual PostgreSQL setup.

#### Backend

See `backend/README.md` for detailed instructions.

```bash
cd backend
./start.sh
```

Or manually:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scoreivy" > .env
python3 -m uvicorn main:app --reload
```

Backend API runs on `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`

## Features

- User authentication and account management
- Question bank management with images and explanations
- Test creation and configuration
- Test taking with timing and auto-grading
- Comprehensive test results with detailed analytics
- Package purchasing system for test access

## Technology Stack

- **Frontend**: Next.js, React, TypeScript
- **Backend**: FastAPI, Python, SQLAlchemy
- **Database**: PostgreSQL

