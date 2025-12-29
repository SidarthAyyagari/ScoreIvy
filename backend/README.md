# ScoreIvy Backend

FastAPI backend service for the ScoreIvy exam platform.

## Quick Start

**Option 1: Use the startup script (easiest)**
```bash
cd backend
./start.sh
```

**Option 2: Manual setup (copy and paste these commands in order)**

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt

# Create .env file with database connection
echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scoreivy" > .env

# Run the server
python3 -m uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

**Note:** Make sure Docker is running and the database is started (see root `README.md` for `docker-compose up -d`)

## Setup Details

1. **Virtual Environment** (recommended to isolate dependencies):
   - Virtual environment is created in the `venv/` directory
   - Activate it with `source venv/bin/activate` before running the server
   - You'll see `(venv)` in your terminal prompt when it's active

2. **Environment Variables**:
   The `.env` file should contain:
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scoreivy
   ```

3. **Database Setup**:
   Make sure PostgreSQL is running. See the `../database/` directory for setup instructions, or use Docker:
   ```bash
   docker-compose up -d
   ```

## API Endpoints

### Questions
- `POST /api/questions/` - Create a single question
- `POST /api/questions/bulk` - Create multiple questions
- `GET /api/questions/` - Get all questions (with optional filtering)
- `GET /api/questions/{question_id}` - Get a specific question
- `DELETE /api/questions/{question_id}` - Soft delete a question

### Tests
- `POST /api/tests/` - Create a new test
- `GET /api/tests/` - Get all tests
- `GET /api/tests/{test_id}` - Get test details (without correct answers)
- `POST /api/tests/{test_id}/attempt` - Submit a completed test attempt
- `GET /api/tests/attempts/{attempt_id}` - Get test attempt details

### Users
- `POST /api/users/` - Create a new user
- `GET /api/users/{user_id}` - Get user by ID

### Packages
- `GET /api/packages/` - Get all active packages
- `GET /api/packages/{package_id}` - Get a specific package

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── app/
│   ├── routers/           # API route handlers
│   │   ├── questions.py
│   │   ├── tests.py
│   │   ├── users.py
│   │   └── packages.py
│   ├── models/            # SQLAlchemy database models
│   │   └── models.py
│   ├── schemas/           # Pydantic schemas for request/response
│   │   └── schemas.py
│   └── db/                # Database configuration
│       └── database.py
└── requirements.txt
```

## TODO

- [ ] Implement proper password hashing (bcrypt)
- [ ] Add authentication/authorization (JWT tokens)
- [ ] Add input validation and sanitization
- [ ] Add comprehensive error handling
- [ ] Add database migrations (Alembic)
- [ ] Add unit tests
- [ ] Add logging
- [ ] Implement file upload for question images

