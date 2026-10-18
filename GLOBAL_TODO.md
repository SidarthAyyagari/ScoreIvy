# ScoreIvy Global TODO

## Rules
- Agents must read this file and [GLOBAL_PLAN.md](GLOBAL_PLAN.md) before starting work.
- Agents must only work on the highest-priority unchecked item assigned to them.
- Agents must not change unrelated files.
- Agents must mark completed items with [x].
- Agents must add new discovered work under Backlog, not randomly implement it.
- Human decides priority changes.

## P0 — Launch: security hardening (Phase 1)
- [x] Verify Google ID tokens server-side (no trusting client-sent email)
- [x] Production config guard (`ENV=production`: required SECRET_KEY/GOOGLE_CLIENT_ID/CORS_ORIGINS, dev login + SKIP_ADMIN_AUTH + free purchase + sample data off, docs hidden)
- [x] Remove student endpoints that edit/delete own packages, attempts, and scores
- [x] Server-side exam sessions: start consumes a credit, server deadline, autosave, resume, server grading over all questions
- [x] No retakes (one attempt per student per test)
- [x] Package credit expiry (`packages.validity_days`, editable in admin)
- [x] Generic 500 errors, login rate limit
- [x] Backend tests for auth + exam/entitlement rules (`backend/tests`)

## P0 — Launch: multi-exam (USMLE + SAT)
- [x] Exams table; packages, tests, sections, questions scoped to an exam; dashboard exam picker
- [x] Question topic tags (`category:name`, per exam) on model, CSV upload, admin UI
- [x] Numeric-entry questions (SAT grid-in; fractions/decimals compared exactly), up to 10 choices (A–J)
- [x] Timed test sections (USMLE blocks / SAT modules) with server-locked deadlines and breaks
- [x] Section and scaled scores (`tests.scoring` lookup tables) on results
- [x] Per-exam tools in exam UI (calculator via Desmos, reference sheet, notes, lab values placeholder)
- [x] Launch both exams together: USMLE Step 1 and SAT (seeded by `database/11_launch_exams_and_orders.sql`)
- [x] Question Bank editor for experts (search/filter, form, tags, save-and-add-another)
- [x] Question history with revert; archive vs. delete (delete only if never served); CSV export/import round trip
- [x] Test Builder: full-length tests from unused questions (Step 1 7×40, SAT 2×27 + 2×22 presets), preview before build
- [x] Real break rules: Step 1 shared 45-min budget, SAT 10-min break between R&W and Math; overrun auto-starts next part
- [ ] Load real question content per exam (Step 1: 280/test, SAT: 98/test)
- [ ] Build tests and create the first packs per exam in production admin
- [ ] Section names are globally unique; scope uniqueness per exam
- [ ] Hide Buy on packs the student already owns
- [ ] Try the full exam flow (both exams) in a browser against real Postgres

## P0 — Launch: payments, hosting, content
- [x] Stripe Checkout for packs + signed webhook that grants the package; refunds revoke credits; orders table + admin view
- [ ] Create Stripe account; test end to end in test mode with `stripe listen`; then live keys + production webhook endpoint
- [ ] Stripe Tax / receipts settings and statement descriptor
- [ ] Alembic baseline migration; stop running SQL scripts on startup
- [x] Dockerfile for backend; Render Blueprint (`render.yaml`) and DEPLOY.md
- [ ] Create the Render Blueprint and deploy (production; staging later)
- [ ] Branch protection on `main` requiring the CI checks
- [ ] Domains, HTTPS, Google OAuth origins, Stripe webhook URL per environment
- [ ] Terms, privacy, refund policy pages
- [ ] Sentry + uptime monitoring + DB backups
- [x] CI: pytest + `next build` for both apps + backend image build (`.github/workflows/ci.yml`)

## P0 — Monday Alpha
- [x] Admin-only access control
- [x] Backend question create API + validation
- [x] Admin question creation form
- [x] Bulk CSV question upload
- [x] CSV validation + error report
- [x] Question list table
- [x] Edit question page
- [x] Exam creation model
- [x] Assign questions to exam
- [x] Student timed exam flow
- [x] Submit exam + score
- [x] Results page
- [ ] Configure `ADMIN_EMAILS` in production OS/environment (comma-separated admin emails; required for admin access after deploy)
- [ ] Production deploy sanity check

## P1 — Soon After
- [ ] Alembic migrations
- [ ] Python docstrings and inline docs across backend (modules, routers, schemas — readability; like Javadoc)
- [ ] Better error handling
- [ ] Loading states
- [x] Search/pagination for admin questions
- [x] Seed demo data
- [ ] Sentry/logging

## Backlog
- [ ] Extend docstrings to frontend TypeScript (JSDoc on shared types and API helpers). All classes and methods should have some small doc explaining what it does. All directories and sub directories should have a small readme explaining what all is happening int it.
- [ ] Admin role management UI (promote/demote users without redeploying ADMIN_EMAILS)
- [x] Document `ADMIN_EMAILS` env var in backend setup notes
- [ ] Align `QuestionUpdate` schema validation with `QuestionCreate` rules
- [ ] API tests for question create validation edge cases
- [x] Admin layout hub page linking question list, create, and CSV upload
- [ ] Wire admin nav link on dashboard when `is_admin` is available from auth
- [x] Publish sample questions CSV template for admins
- [x] API tests for CSV upload validation and import
- [x] Configure `ADMIN_EMAILS` for local dev (shell profile, `.env`, or docker-compose)

- [ ] Pro subscription: in-depth analytics (topic breakdown, timing, score trend, weak-area drills) behind a paywall; packs keep basic grading + score report
- [ ] Real USMLE lab values panel content (currently a placeholder) and text zoom
- [ ] Upgrade backend Python from 3.8 (EOL) to 3.11+
- [ ] SAT adaptive module routing (module 2 difficulty based on module 1 score)
- [ ] Admin form cannot clear a value back to empty (e.g. `validity_days` → no expiry); add an explicit "clear" option
- [ ] Trademark disclaimer (USMLE/NBME, SAT/College Board are not affiliated) on site and legal pages
- [x] Run uvicorn with `--proxy-headers` behind the host's load balancer so rate limits key on the real client IP

## P2 — Later
- [ ] Image upload
- [ ] Advanced analytics
