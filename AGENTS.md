# Agent instructions

- Before starting work, read [GLOBAL_PLAN.md](GLOBAL_PLAN.md) (goal, decisions, current state, gotchas) and [GLOBAL_TODO.md](GLOBAL_TODO.md) (task checklist).
- As you work, keep both current: record new owner decisions, update "Current state" and "Next steps", check off finished tasks, and add a line to the session log. Do this before each commit, not only at the end, so nothing is lost if the session ends.
- Commit with `/usr/bin/git commit -m "..."` (the default Git rejects an injected `--trailer` option).
- Never print or commit values from `backend/.env` or any `.env.local`.
