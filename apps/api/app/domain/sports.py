"""Sport normalization across two upstream vocabularies.

The Socrata facility catalog records sport support as boolean columns
(``regulation_soccer``, ``adult_baseball``, ...). The per-park permit CSV
records it as free-text in a ``Sport or Event Type`` column. This module
maps both representations to the canonical :class:`Sport` enum.
"""

from __future__ import annotations

import re
from typing import Iterable

from app.models import Sport


CATALOG_COLUMN_TO_SPORT: dict[str, Sport] = {
    "regulation_soccer": Sport.SOCCER,
    "nonregulation_soccer": Sport.SOCCER,
    "adult_baseball": Sport.BASEBALL,
    "ll_baseb_12andunder": Sport.BASEBALL,
    "ll_baseb_13andolder": Sport.BASEBALL,
    "adult_softball": Sport.SOFTBALL,
    "ll_softball": Sport.SOFTBALL,
    "adult_football": Sport.FOOTBALL,
    "flagfootball": Sport.FLAG_FOOTBALL,
    "basketball": Sport.BASKETBALL,
    "volleyball": Sport.VOLLEYBALL,
    "tennis": Sport.TENNIS,
    "handball": Sport.HANDBALL,
    "cricket": Sport.CRICKET,
    "lacrosse": Sport.LACROSSE,
    "rugby": Sport.RUGBY,
    "hockey": Sport.HOCKEY,
    "frisbee": Sport.FRISBEE,
    "pickleball": Sport.PICKLEBALL,
    "bocce": Sport.BOCCE,
    "kickball": Sport.KICKBALL,
    "netball": Sport.NETBALL,
}


# Order matters. Patterns are checked top to bottom; the first hit wins.
# Flag football must come before football, etc.
_PERMIT_TEXT_PATTERNS: list[tuple[re.Pattern[str], Sport]] = [
    (re.compile(r"flag\s*football", re.IGNORECASE), Sport.FLAG_FOOTBALL),
    (re.compile(r"football", re.IGNORECASE), Sport.FOOTBALL),
    (re.compile(r"soccer", re.IGNORECASE), Sport.SOCCER),
    (re.compile(r"softball", re.IGNORECASE), Sport.SOFTBALL),
    (re.compile(r"baseball", re.IGNORECASE), Sport.BASEBALL),
    (re.compile(r"basketball", re.IGNORECASE), Sport.BASKETBALL),
    (re.compile(r"volleyball", re.IGNORECASE), Sport.VOLLEYBALL),
    (re.compile(r"tennis", re.IGNORECASE), Sport.TENNIS),
    (re.compile(r"handball", re.IGNORECASE), Sport.HANDBALL),
    (re.compile(r"cricket", re.IGNORECASE), Sport.CRICKET),
    (re.compile(r"lacrosse", re.IGNORECASE), Sport.LACROSSE),
    (re.compile(r"rugby", re.IGNORECASE), Sport.RUGBY),
    (re.compile(r"hockey", re.IGNORECASE), Sport.HOCKEY),
    (re.compile(r"frisbee|ultimate", re.IGNORECASE), Sport.FRISBEE),
    (re.compile(r"pickleball", re.IGNORECASE), Sport.PICKLEBALL),
    (re.compile(r"bocce", re.IGNORECASE), Sport.BOCCE),
    (re.compile(r"kickball", re.IGNORECASE), Sport.KICKBALL),
    (re.compile(r"netball", re.IGNORECASE), Sport.NETBALL),
]


_DISPLAY_LABELS: dict[Sport, str] = {
    Sport.SOCCER: "Soccer",
    Sport.BASEBALL: "Baseball",
    Sport.SOFTBALL: "Softball",
    Sport.FOOTBALL: "Football",
    Sport.FLAG_FOOTBALL: "Flag Football",
    Sport.BASKETBALL: "Basketball",
    Sport.VOLLEYBALL: "Volleyball",
    Sport.TENNIS: "Tennis",
    Sport.HANDBALL: "Handball",
    Sport.CRICKET: "Cricket",
    Sport.LACROSSE: "Lacrosse",
    Sport.RUGBY: "Rugby",
    Sport.HOCKEY: "Hockey",
    Sport.FRISBEE: "Ultimate / Frisbee",
    Sport.PICKLEBALL: "Pickleball",
    Sport.BOCCE: "Bocce",
    Sport.KICKBALL: "Kickball",
    Sport.NETBALL: "Netball",
    Sport.OTHER: "Other",
}


def _is_truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return False


def sports_from_catalog_row(row: dict) -> frozenset[Sport]:
    """Return the set of sports a facility supports given a Socrata row."""
    sports: set[Sport] = set()
    for column, sport in CATALOG_COLUMN_TO_SPORT.items():
        if _is_truthy(row.get(column)):
            sports.add(sport)
    return frozenset(sports)


def sport_from_permit_text(text: str) -> Sport:
    """Map a free-text permit ``Sport or Event Type`` value to a Sport."""
    if not text or not text.strip():
        return Sport.OTHER
    for pattern, sport in _PERMIT_TEXT_PATTERNS:
        if pattern.search(text):
            return sport
    return Sport.OTHER


def display_label(sport: Sport) -> str:
    return _DISPLAY_LABELS[sport]


def all_supported_sports() -> Iterable[Sport]:
    return (s for s in Sport if s is not Sport.OTHER)
