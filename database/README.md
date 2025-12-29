# Database Setup

This directory contains SQL scripts for initializing the ScoreIvy PostgreSQL database.

## Quick Start with Docker

1. **Start the database container**:sh
   docker-compose up -d
   2. **The database will be automatically initialized** with the schema and sample data.

3. **Stop the database**:
   docker-compose down
   4. **View logs**:ash
   docker-compose logs postgres
   The database will be available at `localhost:5432` with:
- Username: `postgres`
- Password: `postgres`
- Database: `scoreivy`

## Database Schema

### Core Tables

- **users**: User accounts
- **sections**: Question categories/sections
- **questions**: Individual test questions with answer choices and explanations
- **packages**: Test packages available for purchase
- **user_packages**: Tracks which packages users have purchased
- **tests**: Test definitions
- **test_questions**: Many-to-many relationship between tests and questions
- **test_attempts**: Records of user test attempts
- **question_attempts**: Individual question responses within a test attempt

## Environment Variables

The backend expects a `DATABASE_URL` environment variable:
```
DATABASE_URL=postgresql://username:password@localhost:5432/scoreivy
```

Create a `.env` file in the `backend/` directory with your database credentials.

