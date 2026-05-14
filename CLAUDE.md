# CLAUDE.md

## Project overview

Field Finder is a take-home project for an AI consulting interview at M-Flat. It is a NYC Parks athletic field availability search tool that aggregates the city's facility catalog and permit feed into a unified calendar view, so users can see availability across many fields and date ranges on a single screen instead of clicking through pins on the official map one by one.

## Stack

- **Backend:** Python 3.11+, FastAPI, httpx, Pydantic v2, SQLite cache, Typer CLI.
- **Frontend:** React + Vite + TypeScript + Tailwind + shadcn/ui + FullCalendar.

## Conventions

- Type hints everywhere.
- Async-first for all I/O.
- No broad `except:` or `except Exception:` clauses — catch specific exceptions.
- Tests live next to the features they cover, not in a separate top-level tree.
- Lint with `ruff`.
- Test with `pytest` and `pytest-asyncio`.

## Working agreements

- Always check [PLAN.md](PLAN.md) to know the current phase. Do not skip ahead.
- Prefer the smallest correct change. Do not over-engineer. Do not add features that were not requested.

## Commit conventions

- Subject line only — no body, no trailers, no AI attribution, no sign-off.
- Conventional-commit style: `feat:`, `chore:`, `docs:`, `fix:`, `refactor:`, `test:`, `ci:`.
- Lowercase subject.
