from typing import Protocol, Mapping, Any, Optional


class FoodSearchClient(Protocol):
    """Protocol client for food search providers (USDA or others)."""

    async def search(self, query: str, *, page_size: Optional[int] = None) -> Mapping[str, Any]:
        """Return a JSON-like mapping containing provider results."""
        pass
