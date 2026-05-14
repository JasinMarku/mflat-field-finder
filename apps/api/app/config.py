"""Application settings loaded from environment / .env file."""

from __future__ import annotations

from datetime import time
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


_APP_DIR = Path(__file__).resolve().parent
_API_DIR = _APP_DIR.parent
_REPO_ROOT = _API_DIR.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    nyc_parks_base_url: str = "https://www.nycgovparks.org"
    nyc_opendata_base_url: str = "https://data.cityofnewyork.us"
    athletic_facilities_dataset: str = "qnem-b8re"

    http_timeout_seconds: float = 15.0
    scrape_max_concurrency: int = 4
    scrape_min_interval_ms: int = 250
    user_agent: str = "MFlatFieldFinder/0.1 (interview prototype)"

    catalog_cache_ttl: int = 86_400
    permits_cache_ttl: int = 21_600
    cache_db_path: Path = Path("./data/cache.sqlite")

    data_mode: Literal["live", "fixtures"] = "live"

    default_day_start: time = time(7, 0)
    default_day_end: time = time(22, 0)

    fixtures_dir: Path = Field(default_factory=lambda: _API_DIR / "fixtures")

    @property
    def permits_csv_url_template(self) -> str:
        return f"{self.nyc_parks_base_url}/permits/field-and-court/issued/{{park_id}}/csv"

    @property
    def socrata_dataset_url(self) -> str:
        return f"{self.nyc_opendata_base_url}/resource/{self.athletic_facilities_dataset}.json"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
