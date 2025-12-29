# ScoreIvy Backend

FastAPI backend service for the ScoreIvy exam platform.

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   Create a `.env` file in the backend directory:
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scoreivy
   ```

3. **Initialize the database**:
   See the `../database/` directory for SQL scripts to set up the database schema.

4. **Run the server**:
   ```bash
   uvicorn main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   API documentation at `http://localhost:8000/docs`

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

