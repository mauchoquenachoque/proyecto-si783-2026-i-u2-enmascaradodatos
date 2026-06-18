import time
from typing import Any, Dict, Iterable, List

import httpx


async def check_service(name: str, url: str, timeout: float = 5.0) -> Dict[str, Any]:
    endpoint = url.rstrip("/") + "/health"
    started = time.perf_counter()
    status = "DOWN"
    error_message = None

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(endpoint)
            response.raise_for_status()
            status = "UP"
    except Exception as exc:
        error_message = str(exc)
    latency_ms = round((time.perf_counter() - started) * 1000, 3)

    result = {
        "service": name,
        "status": status,
        "response_time_ms": latency_ms,
    }
    if error_message:
        result["error"] = error_message
    return result


async def check_services(services: Dict[str, str], timeout: float = 5.0) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for name, url in services.items():
        results.append(await check_service(name, url, timeout=timeout))
    return results
