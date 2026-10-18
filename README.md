# ScoreIvy

An exam platform for creating, taking, and grading multiple-choice tests with OAuth authentication.

## Project Structure

```
ScoreIvy/
├── ui_user/           # Next.js student-facing UI
├── ui_admin/          # Next.js admin/SME UI
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
- 🎨 Student UI (Next.js) on `http://localhost:3000`
- 🛠️ Admin UI (Next.js) on `http://localhost:3001`

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

### Student UI Setup (`ui_user`)

1. **Get Google OAuth Client ID:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google+ API
   - Create OAuth 2.0 credentials
   - Add `http://localhost:3000` and `http://localhost:3001` to authorized JavaScript origins
   - Copy the Client ID

2. **Set environment variable:**
   Create `ui_user/.env.local`:
   ```
   NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id-here
   NEXT_PUBLIC_API_URL=http://localhost:8000
   # Optional: enables the in-exam graphing calculator (free key from desmos.com/api)
   NEXT_PUBLIC_DESMOS_API_KEY=
   ```

3. **Install dependencies:**
   ```bash
   cd ui_user
   npm install
   ```

### Admin UI Setup (`ui_admin`)

Copy the same Google Client ID into `ui_admin/.env.local` (see `ui_admin/.env.local.example`).

### Dev login without Google (LAN / no domain)

Applies to **both** `ui_admin` (:3001) and `ui_user` (:3000).

Google OAuth does not allow raw IP origins (e.g. `http://10.0.0.174:3001`). For local or LAN testing without SSH tunnels:

1. In `backend/.env` set:
   ```
   SKIP_ADMIN_AUTH=true
   ```
2. Restart the backend.
3. Open from any device on your network:
   - Admin: `http://YOUR_LAN_IP:3001`
   - Student: `http://YOUR_LAN_IP:3000`  
   Click **Continue without Google (dev)** on the login page.

Optional:

- `DEV_LOGIN_EMAIL=you@example.com` — which user record dev login uses (default `dev@scoreivy.local`)
- `CORS_EXTRA_ORIGINS=http://10.0.0.174:3001` — only needed if `SKIP_ADMIN_AUTH` is false
- You can keep `NEXT_PUBLIC_API_URL=http://localhost:8000` in `ui_admin/.env.local` — when you open the admin UI via a LAN IP, API calls automatically use that same IP on port `8000`

Run Next.js bound to all interfaces so LAN devices can connect: `cd ui_admin && npm run dev` (already uses `-p 3001`; add `-H 0.0.0.0` if needed).

**Turn `SKIP_ADMIN_AUTH` off before any production deploy.** With `ENV=production` it is ignored and the backend refuses to start if it is set.

### Backend Setup

1. **Set environment variables:**
   Copy `backend/.env.example` to `backend/.env` and fill in `SECRET_KEY`, `GOOGLE_CLIENT_ID`
   (the same client ID as the frontends — the backend verifies Google sign-in tokens with it),
   and `ADMIN_EMAILS`.

2. **Install dependencies:**
   ```bash
   cd backend
   pip3 install -r requirements-dev.txt
   ```

3. **Run tests:**
   ```bash
   cd backend
   python -m pytest
   ```

### Packages, expiry, and exams

- Each package has `validity_days` (editable in the admin UI under Packages). Credits expire that many days after purchase; leave it empty for no expiry. An individual purchase's expiry can be changed under User Packages → `expires_at`.
- Starting a test uses one credit and fixes the deadline on the server. Refreshing resumes the same attempt; answers autosave. Each test can be taken once per student.
- Until Stripe checkout is added, the dashboard "Purchase" button grants packages for free in development only (`ALLOW_FREE_PURCHASE`); it is disabled when `ENV=production`.

### Exams (USMLE, SAT, ...)

One site serves several exams. In the admin UI:

1. **Exams** — create one row per exam (`slug` like `usmle-step-1` or `sat`). `tools` is a JSON list of in-exam tools to show: `"lab_values"`, `"calculator"`, `"reference_sheet"`, `"notes"`.
2. **Sections** — subject areas used for score breakdowns (e.g. Physiology, SAT Math), each with an `exam_id`.
3. **Questions** — set `exam_id`, `section_id`, and `question_type`:
   - `multiple_choice`: `answer_choices` JSON with 2–10 keys from A–J, `correct_answer` is a letter.
   - `numeric_entry`: `answer_choices` `{}`, `correct_answer` like `3/4` or `.75`; extra forms go in `accepted_answers`. Values are compared exactly, so `3/4` matches `0.75`.
   - `tags`: JSON list of `"category:name"` (e.g. `"system:Cardiovascular"`); missing tags are created automatically.
4. **Tests** — set `exam_id`. Optional `scoring` maps raw correct counts to scaled scores: `{"sections": {"<section id>": {"0": 200, "44": 800}}, "overall": {...}}`. Each table uses the highest key that does not exceed the raw count. Without `overall`, the scaled score is the sum of section scaled scores.
5. **Test Sections** — the timed parts of a test (USMLE blocks, SAT modules), with `name` and `time_limit_minutes`. Students take them in order; a submitted or expired part is locked. Between parts they get a break of up to `EXAM_MAX_BREAK_MINUTES` (backend env, default 60). A test with no test sections is a single part timed by the test's `time_limit_minutes`.
6. **Test Questions** — assign questions to a test, with `test_section_id` pointing at the timed part.
7. **Packages** — set `exam_id` so the pack appears under that exam on the student dashboard.

#### CSV question upload

`POST /api/questions/upload?exam_id=<id>` (admin) accepts a CSV with these columns:

| Column | Required | Notes |
| --- | --- | --- |
| `question_text`, `correct_answer` | yes | |
| `choice_a` … `choice_j` | multiple choice | at least two |
| `exam` | no | slug or id; defaults to the `exam_id` query parameter |
| `section_id`, `image_url`, `explanation`, `difficulty` | no | difficulty is easy/medium/hard |
| `question_type` | no | `multiple_choice` (default) or `numeric_entry` |
| `accepted_answers`, `tags` | no | `;`-separated, e.g. `system:Renal;discipline:Physiology` |

The whole file is validated first; nothing is imported if any row has errors.

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
