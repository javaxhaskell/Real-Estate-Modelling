"""Mock listings adapter loading local JSON files."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from src.adapters.base import ListingRecord, ListingsAdapter


class MockListingsAdapter(ListingsAdapter):
    """Read listing data from local JSON for offline demos/tests."""

    def __init__(self, json_path: str | Path) -> None:
        self.json_path = Path(json_path)

    def fetch_listings(self) -> list[ListingRecord]:
        if not self.json_path.exists():
            raise FileNotFoundError(f"Listings JSON not found: {self.json_path}")

        raw = json.loads(self.json_path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("Listings JSON must contain a list of objects")

        listings: list[ListingRecord] = []
        for idx, item in enumerate(raw, start=1):
            try:
                listing_date = item.get("listing_date")
                parsed_date = (
                    dt.datetime.strptime(listing_date, "%Y-%m-%d").date()
                    if listing_date
                    else None
                )
                listings.append(
                    ListingRecord(
                        address=str(item["address"]),
                        postcode=str(item["postcode"]).upper(),
                        lat=float(item["lat"]) if item.get("lat") is not None else None,
                        lon=float(item["lon"]) if item.get("lon") is not None else None,
                        asking_price=float(item["asking_price"]),
                        bedrooms=int(item["bedrooms"]) if item.get("bedrooms") is not None else None,
                        bathrooms=int(item["bathrooms"]) if item.get("bathrooms") is not None else None,
                        property_type=item.get("property_type"),
                        floor_area_sqft=(
                            float(item["floor_area_sqft"])
                            if item.get("floor_area_sqft") is not None
                            else None
                        ),
                        listing_date=parsed_date,
                        source=str(item.get("source", "mock")),
                    )
                )
            except KeyError as exc:
                raise ValueError(f"Listing #{idx} missing required field: {exc}") from exc
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Listing #{idx} has invalid values: {exc}") from exc

        return listings
