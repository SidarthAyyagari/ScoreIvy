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
- A student can't buy a package they already own (unless their copy has expired), because tests can't be retaken.

### Payments (Stripe Checkout)

The dashboard **Buy** button calls `POST /api/payments/checkout/{package_id}`, which creates a pending order and redirects to Stripe Checkout at the package's price. Credits are granted only when Stripe's signed webhook (`POST /api/payments/webhook`) reports the payment as paid. Redirect URLs alone never grant anything. A full refund issued in the Stripe dashboard marks the order refunded and removes the remaining credits. Admins can see every purchase under **Orders**.

Webhook events to enable: `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.expired`, `charge.refunded`.

Local testing with the [Stripe CLI](https://docs.stripe.com/stripe-cli):

```bash
stripe login
stripe listen --forward-to localhost:8000/api/payments/webhook   # prints whsec_...
```

Put your test-mode `STRIPE_SECRET_KEY` (`sk_test_...`) and the printed `STRIPE_WEBHOOK_SECRET` in `backend/.env`, restart the backend, and buy with card `4242 4242 4242 4242`.

Without Stripe keys (development only), **Buy** grants the package immediately (`ALLOW_FREE_PURCHASE`). With `ENV=production` the backend refuses to start without `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and an `https://` `FRONTEND_URL`.

### Exams (USMLE, SAT, ...)

One site serves several exams. USMLE Step 1 and SAT are created automatically (`database/11_launch_exams_and_orders.sql`). Each exam's `tools` (admin → Exams) controls the in-exam tools: `"lab_values"`, `"calculator"`, `"reference_sheet"`, `"notes"`. **Sections** (admin → Sections) are the subject areas used for score breakdowns (e.g. Physiology, SAT Math).

A "test" is a full-length exam in the real format. The usual workflow:

1. **Write questions** in admin → **Question Bank** (or import a CSV, see below).
2. **Build a test** in admin → **Test Builder**: pick the exam, apply the USMLE Step 1 or SAT preset, preview, and build. Optionally add it straight to a package.
3. **Sell it**: the test must be in a package (admin → Packages, with `exam_id` set) for students to see it.

#### Question Bank

- Experts write questions in a form: stem, optional image URL, choices A–J with the correct one marked (or a numeric answer plus other accepted forms), explanation, difficulty, and `category:name` tags. **Save and add another** keeps the exam, section, type, and tags for fast entry.
- **History**: every create, edit, import, archive, restore, revert, and delete is recorded with who did it and when, and any earlier version can be restored with **Revert to this version**. History is kept even after a question is deleted.
- **Delete** permanently removes a question only if no student has ever been served it. Otherwise it is **archived**: it is left out of every test a student starts from then on, while attempts already in progress and past results keep it. Archived questions can be restored.
- **Export CSV** downloads questions (including archived) in the import format, so a file can be re-imported to restore them. Re-imported rows become new questions.

#### Test Builder

Each part (USMLE block, SAT module) has a question count, time limit, and optionally a set of subject sections to draw from. Questions are picked at random from active questions of that exam, split across the allowed sections in proportion to how many each has. By default only questions not already in another test are used, so a student who buys several tests never sees a repeat. **Preview** shows how many questions each part would get and reports any shortfall before anything is saved.

Presets match the real exams:

| Exam | Parts | Breaks |
| --- | --- | --- |
| USMLE Step 1 | 7 blocks × 40 questions, 60 min each | One shared 45-minute budget across all breaks |
| SAT | Reading and Writing 2 × 27 (32 min), Math 2 × 22 (35 min) | None between modules; 10 minutes between Reading and Writing and Math |

Questions needed per full test: Step 1 = 280, SAT = 98.

#### Timing and breaks

Students take parts in order and can't go back to a part once it's submitted or its time runs out. Between parts:

- With a **shared break budget** (`tests.break_pool_minutes`), every break draws from it and unused time carries over.
- Otherwise each part's **break after** (`test_sections.break_after_minutes`) applies; `0` starts the next part immediately. Unset falls back to `EXAM_MAX_BREAK_MINUTES` (backend env, default 60).

When the break runs out, the next part starts automatically, as on test day. A test with no parts is a single part timed by the test's `time_limit_minutes`.

Optional `tests.scoring` maps raw correct counts to scaled scores: `{"sections": {"<section id>": {"0": 200, "44": 800}}, "overall": {...}}`. Each table uses the highest key that does not exceed the raw count. Without `overall`, the scaled score is the sum of section scaled scores.

#### CSV question import

Admin → Question Bank → **Import CSV** (or `POST /api/questions/upload-csv?exam_id=<id>`). Download the template from the import page. Columns:

| Column | Required | Notes |
| --- | --- | --- |
| `question_text`, `correct_answer` | yes | |
| `choice_a` … `choice_j` | multiple choice | at least two |
| `exam` | no | slug or id; defaults to the chosen exam |
| `section_id`, `image_url`, `explanation`, `difficulty` | no | difficulty is easy/medium/hard |
| `question_type` | no | `multiple_choice` (default) or `numeric_entry` |
| `accepted_answers`, `tags` | no | `;`-separated, e.g. `system:Renal;discipline:Physiology` |
| `status` | no | `active` (default) or `archived` |
| `id` | no | written by export; ignored on import |

The whole file is validated first; nothing is imported if any row has errors.

#### Backups

The question bank is protected three ways:

1. **Database backups**: use a managed Postgres with daily backups and point-in-time restore (set up with hosting).
2. **Question history**: undo a bad edit to one question without touching anything else.
3. **CSV export**: a portable copy you can keep anywhere and re-import.

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
