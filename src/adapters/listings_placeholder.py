"""Placeholder for future official listings API integrations."""

from __future__ import annotations

from src.adapters.base import ListingsAdapter


class PlaceholderListingsAPIAdapter(ListingsAdapter):
    """Documented placeholder to integrate official APIs in the future."""

    def __init__(self, provider_name: str, api_base_url: str | None = None) -> None:
        self.provider_name = provider_name
        self.api_base_url = api_base_url

    def fetch_listings(self) -> list:
        raise NotImplementedError(
            "No live integration is implemented. Use an official API contract from "
            f"{self.provider_name} and map responses into ListingRecord objects. "
            "This project intentionally avoids scraping protected listing websites."
        )
