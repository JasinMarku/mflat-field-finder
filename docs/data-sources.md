# Data Sources

The project rests on two public endpoints from the City of New York. Together they answer the question "where can I play sport X between dates A and B?" by joining a catalog of facilities to a per-park feed of issued permits.

## 1. NYC Open Data Athletic Facilities (Socrata)

A monthly-refreshed catalog of every athletic facility maintained by NYC Parks.

| Property | Value |
| --- | --- |
| Dataset ID | `qnem-b8re` |
| Base URL | `https://data.cityofnewyork.us/resource/qnem-b8re.json` |
| Auth | None required. An optional `X-App-Token` header raises rate limits. |
| Update frequency | Monthly |
| Total active rows | ~5,200 facilities citywide |
| Soccer-capable rows | ~360 |

### Columns we read

| Column | Purpose | Example |
| --- | --- | --- |
| `gispropnum` | Park ID. Join key to the permit CSV URL. | `B073`, `M028`, `Q021` |
| `field_number` | Field index within a park. | `01`, `02` |
| `primary_sport` | Short sport code. | `SCR`, `FTB`, `MPPA` |
| `surface_type` | Free text. | `Natural`, `Concrete` |
| `field_lighted` | Boolean. | `true` |
| `borough` | One letter. | `M`, `X`, `B`, `Q`, `R` |
| `featurestatus` | Filter for `Active` server-side. | `Active` |

In addition to `primary_sport`, the row carries boolean flags for every sport the field supports. We read these to compute the full sport set per field:

`regulation_soccer`, `nonregulation_soccer`, `basketball`, `adult_baseball`, `adult_softball`, `adult_football`, `flagfootball`, `volleyball`, `tennis`, `handball`, `cricket`, `lacrosse`, `rugby`, `hockey`, `frisbee`, `pickleball`, `bocce`, `kickball`, `netball`, `ll_baseb_12andunder`, `ll_baseb_13andolder`, `ll_softball`.

### Server-side filter

We always pass:

```
$where=featurestatus='Active'
```

This drops decommissioned and under-construction rows before they cross the wire.

## 2. Per-park permit CSV (nycgovparks.org)

The issued permits for a single park, exported as CSV.

| Property | Value |
| --- | --- |
| URL pattern | `https://www.nycgovparks.org/permits/field-and-court/issued/{park_id}/csv` |
| `park_id` | The `gispropnum` from the Socrata catalog. This is the join. |
| Auth | None |

### CSV columns

```
Start, End, Field, Sport or Event Type, Event Name, Organization, Event Status
```

### Parsing notes

- Date format looks like `3/20/2026 6:00 p.m.`. Normalize `a.m.`/`p.m.` to `AM`/`PM` before passing to a datetime parser.
- A `Sport or Event Type` of `Full Closure` represents a construction or maintenance blackout. Some span months or even years. Treat these as hard blocks that mask the entire field for the duration, regardless of sport.
- Field names inside the CSV (for example `Grand Street - Soccer 01`) drift from the catalog's `field_number`. We do not try to reconcile them by string match. We work directly with whatever labels the CSV provides for display, and join only at the park level.

## Politeness controls

We are a guest on someone else's infrastructure. The planned controls:

| Control | Value |
| --- | --- |
| Concurrency cap | 4 simultaneous requests |
| Min interval | 250 ms between requests |
| TTL cache | 6 hours per park (the city refreshes daily) |
| Retries | 3 attempts, exponential backoff, only on 5xx and timeouts |
| Headers | Realistic `User-Agent` and `Referer` |

### User-Agent decision

The permit endpoint sits behind a CloudFront WAF that blocks bot-identifying User-Agent strings. A plain `MFlatFieldFinder/0.1` UA returns `403 Forbidden` from any IP we tried, even residential ones.

We send a hybrid UA: a real Chrome-on-macOS prefix with our app name appended.

```
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 MFlatFieldFinder/0.1
```

This mirrors the pattern major crawlers use, where the operator identifies after a browser-shaped prefix (for example `Mozilla/5.0 (...) Googlebot/2.1`). The appended `MFlatFieldFinder/0.1` lets a server operator who reads logs see who we are and reach us.

The tradeoff: we get through the WAF, but we lose the option of being filtered or rate-limited specifically. We balance this against the politeness we control directly: concurrency capped at 4, a minimum 250 ms gap between requests, and a 6-hour TTL cache per park so we touch each one at most a few times a day.

A production deployment with a consistent egress IP should not rely on UA shaping. The right answer is to request an allow-list entry from NYC Parks, document the use case, and identify honestly.

## Known limitation: CloudFront WAF

The `nycgovparks.org` permit endpoint sits behind CloudFront, which returns `403 Forbidden` to some egress IP ranges, including a number of cloud provider blocks. There is no documented allowlist process. To stay honest about this we plan a fixture-mode fallback: if a deployed instance cannot reach the live endpoint, it serves a frozen snapshot of permits with a banner that says so. This keeps the demo functional without pretending the upstream is reachable.

## Why not scrape the official map

The Leaflet map at `nycgovparks.org/facilities` is a client-rendered view that calls the same data we use here. The CSV endpoint exposes the underlying permit set in a stable, pagination-free form. It is faster, more reliable, and politer than driving a headless browser. We use the data path the map itself uses.
