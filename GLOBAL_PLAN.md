# ScoreIvy Global Plan

The handoff document for this project. A new agent session should be able to read this file and continue without any earlier chat history. Keep it current: update it whenever a decision is made or a piece of work lands.

- **This file**: goal, product decisions, current state, how the code fits together, gotchas, roadmap, session log.
- **[GLOBAL_TODO.md](GLOBAL_TODO.md)**: the checklist of individual tasks.
- **[README.md](README.md)**: setup, environment variables, and how admins use the site.

Last updated: 2026-10-18 (after commit `76af38d`).

## Goal

A live, secure, paid website where students take full-length practice tests for **USMLE Step 1** and the **SAT**, on one site. The owner's mom and other doctor experts write the questions in the admin site.

## Product decisions (made by the owner)

| Topic | Decision |
| --- | --- |
| Exams at launch | USMLE **Step 1 only** and SAT, launched together on one site |
| What's sold | **Test packs**: a number of test credits, including grading and a basic score report |
| Credit expiry | Pack credits expire; expiry is set per package in admin (`packages.validity_days`, empty = never) |
| Retakes | Not allowed: one attempt per student per test |
| Subscription | **Parked.** Later, a subscription unlocks in-depth analysis and focused areas of improvement. Packs keep basic grading and the score report |
| What a "test" is | A full-length exam in the real format: same timing, same restrictions, and no going back to earlier sections |
| SAT format | Fixed modules for now; adaptive module 2 comes later |
| Question source | Experts type questions into the admin site. Generating or scraping questions may come later |
| Admin trust | All admins are trusted to edit the bank for now. Guardrails are history, undo, safe delete, and CSV backups rather than permissions |
| Feature gating | Build everything first, then decide what goes behind which paywall |
| Payments | Stripe Checkout |

### Real exam formats the builder matches

| Exam | Parts | Breaks | Questions per full test |
| --- | --- | --- | --- |
| USMLE Step 1 | 7 blocks × 40 questions, 60 min each | One 45-minute budget shared across all breaks | 280 |
| SAT | Reading and Writing: 2 modules × 27 (32 min). Math: 2 modules × 22 (35 min) | None between modules; 10 minutes between Reading and Writing and Math | 98 |

A student must never see a repeat question across the tests they buy, so the Test Builder by default only uses questions that aren't in another test. Three Step 1 tests need 840 unique questions; five SAT tests need 490.

## Current state

**Built and committed** (all 57 backend tests pass; both Next.js apps build for production):

- **Security**: server-side Google sign-in verification, admin-only routes, production config checks, rate limits, generic error responses.
- **Exams and content**: USMLE Step 1 and SAT seeded; subject sections; tags; multiple-choice (A–J) and numeric-entry questions; per-exam tools (calculator, reference sheet, notes, lab values placeholder).
- **Taking a test**: server-controlled sessions with deadlines, autosave, resume, server grading, timed parts locked once finished, scaled scores and a section breakdown on results.
- **Breaks**: Step 1 uses a shared budget; SAT uses scheduled breaks. When a break runs out, the next part starts automatically.
- **Payments**: Stripe Checkout and a signed webhook grant the pack. Abandoned checkouts expire, refunds revoke credits, and there's an orders view in admin. Without Stripe keys in dev, buying grants the pack immediately.
- **Admin Question Bank**: an editor for experts, search and filters, history with revert, archive vs. delete, CSV import and export.
- **Admin Test Builder**: builds full-length tests from unused questions using the presets above, with a preview before building.

**Not yet done:**

- Nothing has been tried in a browser or against a real Postgres database since the large changes; only automated tests and builds.
- No hosting yet; the site only runs locally.
- No real questions loaded.
- No Stripe account set up.

## Next steps, in order

1. Click through both exams end to end locally against Postgres (student and admin); fix what breaks.
2. Small fixes: hide Buy on packs a student already owns; make subject section names unique per exam instead of globally.
3. Hosting: Dockerfile for the backend, deploy both frontends and the backend, managed Postgres with daily backups and point-in-time restore, domains, HTTPS, Google OAuth origins, uvicorn `--proxy-headers`.
4. Stripe: create the account, test end to end in test mode with `stripe listen`, then live keys and the production webhook.
5. Legal pages (terms, privacy, refund policy) and a trademark disclaimer (not affiliated with NBME, USMLE, or College Board).
6. Monitoring: Sentry and uptime checks. CI running pytest and both `next build`s.
7. Content: experts load questions, build tests, create packs in production admin.

Later: the subscription for in-depth analysis, adaptive SAT, real lab values content, Alembic migrations, a Python upgrade from 3.8.

## How the code fits together

| Piece | Where | Notes |
| --- | --- | --- |
| Backend | `backend/` | FastAPI, SQLAlchemy 2.0, Pydantic v2, Postgres. Python 3.8 virtualenv at `backend/venv` |
| Student site | `ui_user/` | Next.js 14, port 3000 |
| Admin site | `ui_admin/` | Next.js 14, port 3001 |
| Database migrations | `database/NN_*.sql` | Run at backend startup from the list in `backend/main.py`. Add new files there. Latest is `13` |
| Tests | `backend/tests/` | `cd backend && source venv/bin/activate && python -m pytest -q` |

Key backend modules:

- `app/services/exam_session.py`: starting a test, timed parts, breaks (`break_allowance`, `advance`), grading. An attempt stores the question ids it was started with, so archiving a question never changes a test in progress.
- `app/services/payments.py` and `app/routers/payments.py`: Stripe checkout, webhook, refunds.
- `app/services/questions.py` and `app/routers/questions.py`: the question bank API at `/api/questions` (admin only). Every change writes a `QuestionRevision` snapshot with who and when.
- `app/services/question_csv.py`: CSV import and export.
- `app/services/test_builder.py`: the Test Builder; endpoints `/api/admin/test-builder` and `/api/admin/test-builder/pool`.
- `app/config.py`: environment settings and production checks.

Key admin pages: `ui_admin/app/(protected)/questions/` (bank, editor, import), `ui_admin/app/(protected)/test-builder/`, and the generic table pages driven by `ui_admin/app/lib/resources.ts`.

Rules worth knowing:

- Deleting a question removes it permanently only if no student was ever served it; otherwise it's archived.
- Reverting restores a question's content but not its archived status.
- Buying a pack you already own (and that hasn't expired) is refused.
- A test only shows to students if it's in a package with the exam set.

## Gotchas for agents

- **Commits**: the local Git is 2.24 and the environment adds a `--trailer` option it doesn't support. Commit with `/usr/bin/git commit -m "..."`.
- **Secrets**: `backend/.env` and the `.env.local` files are gitignored. Never print or commit their values.
- **Test database**: tests use SQLite with autoflush off, so call `db.flush()` before relying on new ids. `pytest.ini` sets `python_classes = *Suite` so the `Test*` database models aren't collected as tests. `conftest.py` turns off Stripe and rate limiting.
- **Next.js**: pages using `useSearchParams` need a `<Suspense>` wrapper or `next build` fails.
- **Clearing fields**: `update_question` only clears a field when it's in `NULLABLE_FIELDS`; other `None` values are ignored.

## Session log

Newest first. Add a line or two per working session.

- **2026-10-18** — Question Bank editor, history and revert, archive vs. delete, CSV export; Test Builder with USMLE and SAT presets; real break rules; student break screen explains shared vs. scheduled breaks. Commit `76af38d`. Created this plan and `AGENTS.md`.
- **2026-10-18** — Stripe Checkout for packs (commit `74142ce`).
- **2026-10-18** — Security hardening, server-side exam sessions, credit expiry, no retakes, multi-exam support for USMLE and SAT (commit `01a984d`).
