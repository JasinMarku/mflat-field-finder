# Plan

- [x] **Phase 0: repo skeleton and plan**
  - Deliverable: `.gitignore`, `README.md`, `PLAN.md`, `CLAUDE.md` committed to a fresh repo.

- [x] **Phase 1: data source recon and architecture docs**
  - Deliverable: `docs/architecture.md` and `docs/data-sources.md` describing the Socrata facility catalog, permit CSV feed, refresh cadence, and end-to-end request flow.

- [x] **Phase 2: domain models, config, sport normalization**
  - Deliverable: Pydantic v2 models for `Facility`, `Permit`, `AvailabilityWindow`; settings module; sport-name normalization table with tests.

- [x] **Phase 3: SQLite TTL cache + Socrata facility catalog client**
  - Deliverable: async httpx client for the Socrata catalog wrapped in a SQLite-backed TTL cache, with a Typer command to refresh.

- [x] **Phase 4: permit CSV fetcher with politeness controls**
  - Deliverable: permit CSV fetcher with retry/backoff, per-host rate limiting, ETag/Last-Modified handling, and persisted records.

- [x] **Phase 5: availability algorithm (interval inversion)**
  - Deliverable: pure function that inverts permit intervals against facility open hours to produce available windows; unit tests covering overlaps, day boundaries, and timezone edges.

- [x] **Phase 6: FastAPI HTTP endpoints**
  - Deliverable: `/facilities`, `/availability`, `/health` endpoints with query validation, OpenAPI docs, and integration tests.

- [x] **Phase 7: React + Vite + Tailwind frontend**
  - Deliverable: single-page app with filters (sport, borough, date range) rendering a unified availability matrix across selected fields. (We replaced FullCalendar resource-timeline with a lighter custom matrix; it scales to 300+ rows and is more scannable for "compare many fields" than FullCalendar's paid plugin.)
  - 7a complete: Vite + React + TS + Tailwind scaffold with QueryBar wired to `/api/sports` and `/api/availability` via the Vite dev proxy; results summary card renders.
  - 7b complete: availability matrix (field x day grid with free/busy segments) and per-facility detail drawer with day-by-day permit and free listings.
  - 7c complete: borough filter, sport permit-density banner, expanded field labels (e.g. "Pkb 04" → "Pickleball Court 04"), date-range guardrails, loading skeleton, and result footer.

- [x] **Phase 8: Dockerfile and Render deploy**
  - Deliverable: production Dockerfile, Render service config, and a live URL.

- [ ] **Phase 9: README polish and walkthrough script**
  - Deliverable: final README with screenshots, architecture diagram, and a recorded/walkthrough script for the interview.
