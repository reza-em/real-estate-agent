"""Compatibility exports for code using the original module path."""

import sqlite3
from pathlib import Path

from app.db.repository import DEFAULT_DB_PATH, ListingRepository
from app.models.listing import Listing


DB_PATH = DEFAULT_DB_PATH


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    return ListingRepository(path).connect()


def save_listings(listings: list[Listing], path: Path = DB_PATH) -> None:
    ListingRepository(path).save(listings)


__all__ = ["DB_PATH", "connect", "save_listings"]
