# Field Finder

Live: https://mflat-field-finder.onrender.com
(Free-tier instance; first request after idle may take ~30s to wake.)

Take-home for an AI consulting interview at M-Flat. A NYC Parks athletic field availability search tool that replaces the official map's pin-by-pin, date-by-date workflow with a unified calendar showing many fields across wide date ranges on a single screen.

Status: in progress (see [PLAN.md](PLAN.md))

## Quick start

Coming soon.

## Run with Docker

One command, no Node or Python toolchain required:

```sh
docker build -t fieldfinder .
docker run -p 8000:8000 fieldfinder
# then open http://localhost:8000
```

The container builds the React frontend and serves it from the FastAPI process. No separate web server needed.

## Screenshots

![Availability matrix](docs/images/matrix.png)

![Facility detail drawer](docs/images/drawer.png)

## Architecture

See [docs/architecture.md](docs/architecture.md).

## Data sources

See [docs/data-sources.md](docs/data-sources.md).

## License

MIT
