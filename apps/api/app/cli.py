"""Typer CLI for ops and verification."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from app.cache import TTLCache
from app.clients.socrata import SocrataClient
from app.config import get_settings
from app.domain.sports import all_supported_sports, display_label
from app.models import Sport


app = typer.Typer(help="Field Finder CLI", no_args_is_help=True)
console = Console()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@app.command()
def sports() -> None:
    """List supported sports."""
    table = Table(title="Supported sports")
    table.add_column("Code")
    table.add_column("Label")
    for sport in all_supported_sports():
        table.add_row(sport.value, display_label(sport))
    console.print(table)


@app.command()
def catalog(
    sport: Optional[str] = typer.Option(None, help="Filter by sport code"),
    limit: int = typer.Option(20, help="Rows to print"),
    refresh: bool = typer.Option(False, help="Force re-fetch, ignore cache"),
) -> None:
    """Fetch the facility catalog and print a summary."""
    asyncio.run(_catalog(sport, limit, refresh))


async def _catalog(sport: Optional[str], limit: int, refresh: bool) -> None:
    settings = get_settings()
    cache = TTLCache(settings.cache_db_path)
    client = SocrataClient(settings, cache)
    facilities = await client.get_all_facilities(force_refresh=refresh)
    if sport:
        target = Sport(sport)
        facilities = [f for f in facilities if target in f.sports]

    table = Table(title=f"Facilities ({len(facilities)} matching)")
    table.add_column("Facility ID")
    table.add_column("Park")
    table.add_column("Borough")
    table.add_column("Label")
    table.add_column("Sports")
    table.add_column("Surface")
    table.add_column("Lit")
    for facility in facilities[:limit]:
        sport_list = ", ".join(sorted(s.value for s in facility.sports))
        table.add_row(
            facility.facility_id,
            facility.park_id,
            facility.borough.label,
            facility.field_label,
            sport_list,
            facility.surface_type or "",
            "yes" if facility.is_lighted else "no",
        )
    console.print(table)


@app.command("cache-clear")
def cache_clear(
    namespace: str = typer.Argument(..., help="Cache namespace to purge"),
) -> None:
    """Clear a cache namespace."""
    settings = get_settings()
    cache = TTLCache(settings.cache_db_path)
    n = cache.purge_namespace(namespace)
    console.print(f"Purged {n} entries from namespace '{namespace}'")


if __name__ == "__main__":
    app()
