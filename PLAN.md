# Plan

- [x] **Phase 0: repo skeleton and plan**
  - Deliverable: `.gitignore`, `README.md`, `PLAN.md`, `CLAUDE.md` committed to a fresh repo.

- [x] **Phase 1: data source recon and architecture docs**
  - Deliverable: `docs/architecture.md` and `docs/data-sources.md` describing the Socrata facility catalog, permit CSV feed, refresh cadence, and end-to-end request flow.

- [x] **Phase 2: domain models, config, sport normalization**
  - Deliverable: Pydantic v2 models for `Facility`, `Permit`, `AvailabilityWindow`; settings module; sport-name normalization table with tests.

- [x] **Phase 3: SQLite TTL cache + Socrata facility catalog client**
  - Deliverable: async httpx client for the Socrata catalog wrapped in a SQLite-backed TTL cache, with a Typer command to refresh.

- [ ] **Phase 4: permit CSV fetcher with politeness controls**
  - Deliverable: permit CSV fetcher with retry/backoff, per-host rate limiting, ETag/Last-Modified handling, and persisted records.

- [ ] **Phase 5: availability algorithm (interval inversion)**
  - Deliverable: pure function that inverts permit intervals against facility open hours to produce available windows; unit tests covering overlaps, day boundaries, and timezone edges.

- [ ] **Phase 6: FastAPI HTTP endpoints**
  - Deliverable: `/facilities`, `/availability`, `/health` endpoints with query validation, OpenAPI docs, and integration tests.

- [ ] **Phase 7: React + Vite + Tailwind + FullCalendar frontend**
  - Deliverable: single-page app with filters (sport, borough, date range) rendering a unified FullCalendar view across selected fields.

- [ ] **Phase 8: Dockerfile and Render deploy**
  - Deliverable: production Dockerfile, Render service config, and a live URL.

- [ ] **Phase 9: README polish and walkthrough script**
  - Deliverable: final README with screenshots, architecture diagram, and a recorded/walkthrough script for the interview.
