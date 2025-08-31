import httpx

_client: httpx.AsyncClient | None = None


async def startup_client():
    global _client
    _client = httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0))


async def shutdown_client():
    global _client
    if _client:
        await _client.aclose()
        _client = None


def get_client() -> httpx.AsyncClient:
    assert _client is not None, "HTTP client not initialized"
    return _client
