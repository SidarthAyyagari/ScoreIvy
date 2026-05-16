# ScoreIvy Global TODO

## Rules
- Agents must read this file before starting work.
- Agents must only work on the highest-priority unchecked item assigned to them.
- Agents must not change unrelated files.
- Agents must mark completed items with [x].
- Agents must add new discovered work under Backlog, not randomly implement it.
- Human decides priority changes.

## P0 — Monday Alpha
- [x] Admin-only access control
- [ ] Backend question create API + validation
- [ ] Admin question creation form
- [ ] Bulk CSV question upload
- [ ] CSV validation + error report
- [ ] Question list table
- [ ] Edit question page
- [ ] Exam creation model
- [ ] Assign questions to exam
- [ ] Student timed exam flow
- [ ] Submit exam + score
- [ ] Results page
- [ ] Configure `ADMIN_EMAILS` in production OS/environment (comma-separated admin emails; required for admin access after deploy)
- [ ] Production deploy sanity check

## P1 — Soon After
- [ ] Alembic migrations
- [ ] Better error handling
- [ ] Loading states
- [ ] Search/pagination for admin questions
- [ ] Seed demo data
- [ ] Sentry/logging

## Backlog
- [ ] Configure `ADMIN_EMAILS` for local dev (shell profile, `.env`, or docker-compose)
- [ ] Admin role management UI (promote/demote users without redeploying ADMIN_EMAILS)
- [ ] Document `ADMIN_EMAILS` in backend setup / deploy notes

## P2 — Later
- [ ] Stripe
- [ ] Image upload
- [ ] Advanced analytics
- [ ] Legal pages
