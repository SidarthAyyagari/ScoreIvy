# ScoreIvy

An exam platform for creating, taking, and grading multiple-choice tests.

## Project Structure

```
ScoreIvy/
├── frontend/          # Next.js React frontend application
├── backend/           # FastAPI Python backend service
└── database/          # PostgreSQL database initialization scripts
```

## Getting Started

### Frontend

See `frontend/README.md` for frontend setup instructions.

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`

### Backend

See `backend/README.md` for backend setup instructions.

```bash
cd backend
pip3 install -r requirements.txt
uvicorn main:app --reload
```

Backend API runs on `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### Database

See `database/README.md` for database setup instructions.

1. Create PostgreSQL database
2. Run initialization scripts from `database/` directory

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

