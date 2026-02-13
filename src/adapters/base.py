"""Adapter interfaces and shared records."""

from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class ListingRecord:
    address: str
    postcode: str
    lat: float | None
    lon: float | None
    asking_price: float
    bedrooms: int | None
    bathrooms: int | None
    property_type: str | None
    floor_area_sqft: float | None
    listing_date: dt.date | None
    source: str


class ListingsAdapter(ABC):
    """Contract for listing providers.

    Real listing integrations should be implemented through explicit APIs.
    This project intentionally avoids scraping sources that may prohibit it.
    """

    @abstractmethod
    def fetch_listings(self) -> list[ListingRecord]:
        """Return listing records from the configured source."""
