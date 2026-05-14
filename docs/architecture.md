# Architecture

## System diagram

```
┌─────────────┐      HTTPS       ┌──────────────────────────────────────┐
│   Browser   │ ───────────────> │              FastAPI                 │
│  React UI   │ <─────────────── │  /api/facilities  /api/availability  │
└─────────────┘    JSON          └───────────────────┬──────────────────┘
                                                     │
                              ┌──────────────────────┴──────────────────┐
                              │                                         │
                              ▼                                         ▼
                  ┌────────────────────────┐              ┌──────────────────────┐
                  │     SocrataClient      │              │     PermitClient     │
                  │  catalog of facilities │              │  per-park permit CSV │
                  └───────────┬────────────┘              └──────────┬───────────┘
                              │                                      │
                              └──────────────┬───────────────────────┘
                                             ▼
                                  ┌────────────────────┐
                                  │   SQLite cache     │
                                  │   TTL per entry    │
                                  └──────────┬─────────┘
                                             │
                              ┌──────────────┴──────────────┐
                              ▼                             ▼
                  ┌────────────────────────┐    ┌──────────────────────────┐
                  │  data.cityofnewyork.us │    │   www.nycgovparks.org    │
                  │       (Socrata)        │    │  /permits/.../{park}/csv │
                  └────────────────────────┘    └──────────────────────────┘
```

## Module layout

Most of this does not exist yet. It is the target shape for Phases 2 through 6.

```
apps/api/app/
├── config.py            settings from env (pydantic-settings)
├── models.py            Facility, Permit, TimeWindow, Sport enum, Borough enum
├── cache.py             SQLite TTL cache
├── clients/
│   ├── socrata.py       facility catalog
│   └── permits.py       per-park CSV
├── domain/
│   ├── sports.py        normalization across catalog + CSV vocabularies
│   └── availability.py  interval inversion (the only real algorithm)
├── routes/              FastAPI endpoints (Phase 6)
└── cli.py               Typer CLI for ops and verification
```

## Request lifecycle

For `GET /api/availability?sport=soccer&from=...&to=...`:

1. Load the facility catalog from the cache, falling back to Socrata on miss.
2. Filter facilities by sport and borough.
3. Group the remaining facilities by `park_id`.
4. Fan-out fetch permits for each park, concurrent but rate-limited, cached for 6 hours.
5. For each facility, run `compute_free_slots(permits, range, hours)` to invert busy intervals into free windows.
6. Sort the results by total free hours descending and return JSON.

Cold path estimate: about 80 parks at 250 ms each, with concurrency of 4, comes out to roughly 5 seconds. Warm path: sub-second, since both the catalog and recent permit pulls are in the cache.

## Stack choices

- **FastAPI**: async, OpenAPI for free, Pydantic-native.
- **httpx (async)**: real async HTTP with a sensible API.
- **SQLite**: zero-ops cache, one file, easy to inspect, swappable for Redis later.
- **Typer + Rich**: CLI to verify the data layer independently of the API.
- **Vite + React + Tailwind + shadcn/ui**: production-grade UI baseline.
- **FullCalendar resource-timeline**: exactly the "many fields by time" view the brief asks for.

## Tradeoffs we are making explicitly

| Decision | Cost | Why we accept it |
| --- | --- | --- |
| SQLite over Redis | Single-writer, no clustering | Simpler ops; fine for one process at this scale |
| CSV endpoint over headless browser | Tied to one upstream URL | Faster, more reliable, politer |
| Default operating hours 7am to 10pm | Real hours vary by facility | Configurable later; close enough for the demo |
| Single Socrata fetch for the whole catalog | Slightly more bytes per refresh | ~5,000 rows is small; per-row queries cost more in latency than they save in bandwidth |

## Hardening for a year-long deployment

The shape we would move to if this ran beyond the interview window:

- Move the cache to Redis so multiple API workers can share it.
- Add a background warmer (apscheduler) that refreshes popular sports nightly.
- Wire a cache invalidation hook to the upstream "Permit information last updated" marker.
- Solve the CloudFront 403 problem with a residential egress proxy, or a partnership with NYC Parks.
- Observability: structured logs, OpenTelemetry traces, per-park latency metrics.
- Add auth if NYC Parks publishes a real API.
- Keep an audit log of every external request, so politeness is verifiable, not just claimed.
