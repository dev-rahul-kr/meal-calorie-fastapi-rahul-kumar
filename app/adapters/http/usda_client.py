import httpx
import asyncio
from typing import Any, Mapping, Optional, Tuple
from cachetools import TTLCache
from app.core.config import get_settings


class USDAError(RuntimeError):
    pass


class USDAClient:
    """ HTTP client (Async) for USDA FoodData Central search with TTL cache."""

    def __init__(
        self,
        *,
        client: Optional[httpx.AsyncClient] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_s: Optional[float] = None,
        retries: Optional[int] = None,
        default_page_size: Optional[int] = None,
        cache_ttl_s: Optional[int] = None,
        cache_maxsize: Optional[int] = None,
    ):
        settings = get_settings()
        self._base_url = base_url or settings.USDA_BASE_URL
        self._api_key = (api_key or settings.USDA_API_KEY.get_secret_value())
        self._timeout_s = float(timeout_s or settings.USDA_TIMEOUT_S)
        self._retries = int(retries or settings.USDA_RETRIES)
        self._default_page_size = int(default_page_size or settings.USDA_PAGE_SIZE)
        self._client = client or httpx.AsyncClient(timeout=self._timeout_s)
        ttl = settings.CACHE_TTL_S if cache_ttl_s is None else cache_ttl_s
        maxsize = settings.CACHE_MAXSIZE if cache_maxsize is None else cache_maxsize
        self._cache: Optional[TTLCache[Tuple[str, int], Mapping[str, Any]]] = (
            TTLCache(maxsize=maxsize, ttl=ttl) if ttl and ttl > 0 else None
        )
        self._lock = asyncio.Lock()  # protect cache in concurrent scenarios

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def retries(self) -> int:
        return self._retries

    @property
    def timeout_s(self) -> float:
        return self._timeout_s

    async def search(self, query: str, *, page_size: Optional[int] = None) -> Mapping[str, Any]:
        """Call USDA search endpoint and return JSON. Uses TTL cache when enabled."""
        keys = (query.strip().lower(), int(page_size or self._default_page_size))

        if self._cache is not None:
            result = self._cache.get(keys)
            if result is not None:
                return result

        params = {"query": query, "api_key": self._api_key, "pageSize": keys[1]}

        last_exc: Optional[Exception] = None
        for attempt in range(self._retries + 1):
            try:
                resp = await self._client.get(self._base_url, params=params)
                if resp.status_code == 404:
                    data = {"foods": []}
                else:
                    resp.raise_for_status()
                    data = resp.json()

                # store in cache (including empty lists) to avoid refetch storms
                if self._cache is not None:
                    async with self._lock:
                        self._cache[keys] = data
                return data

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                last_exc = e
                if attempt < self._retries:
                    await asyncio.sleep(0.3 * (attempt + 1))
                else:
                    break

        raise USDAError(f"USDA request failed after {self._retries + 1} attempts") from last_exc

    async def aclose(self) -> None:
        await self._client.aclose()


_singleton: Optional[USDAClient] = None

def get_usda_client() -> USDAClient:
    global _singleton
    if _singleton is None:
        _singleton = USDAClient()
    return _singleton
