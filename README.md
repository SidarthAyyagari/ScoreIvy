# ScoreIvy

An exam platform for creating, taking, and grading multiple-choice tests with OAuth authentication.

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

## Setup Instructions

### Prerequisites

- Docker and Docker Compose
- Node.js and npm
- Python 3.8+
- Google OAuth Client ID (for authentication)

### Frontend Setup

1. **Get Google OAuth Client ID:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google+ API
   - Create OAuth 2.0 credentials
   - Add `http://localhost:3000` to authorized JavaScript origins
   - Copy the Client ID

2. **Set environment variable:**
   Create `frontend/.env.local`:
   ```
   NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id-here
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

### Backend Setup

1. **Set environment variables:**
   Create `backend/.env`:
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scoreivy
   SECRET_KEY=your-secret-key-here-change-in-production
   ```

2. **Install dependencies:**
   ```bash
   cd backend
   pip3 install -r requirements.txt
   ```

### Database Setup

The database is automatically initialized when you run `docker-compose up -d`.

To manually initialize:
```bash
docker exec -it scoreivy-postgres psql -U postgres -d scoreivy -f /docker-entrypoint-initdb.d/01_init_database.sql
docker exec -it scoreivy-postgres psql -U postgres -d scoreivy -f /docker-entrypoint-initdb.d/02_sample_data.sql
```

## Features

- ✅ OAuth authentication (Google)
- ✅ User account management
- ✅ Package purchasing system
- ✅ Question bank management with images and explanations
- ✅ Test creation and configuration
- ✅ Test taking with timing and auto-grading
- ✅ Comprehensive test results with detailed analytics
- ✅ Package-based test access control

## API Documentation

Once the backend is running, visit:
- `http://localhost:8000/docs` - Interactive API documentation (Swagger UI)
- `http://localhost:8000/redoc` - Alternative API documentation

## Technology Stack

- **Frontend**: Next.js, React, TypeScript, Google OAuth
- **Backend**: FastAPI, Python, SQLAlchemy, JWT authentication
- **Database**: PostgreSQL (Docker)
