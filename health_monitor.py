from typing import Any, Dict, Iterable, List

from database_health import check_database_health_batch
from service_checker import check_services
from system_metrics import collect_system_metrics


def collect_health_snapshot(services: Dict[str, str], connections: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    system = collect_system_metrics()
    return {
        "system": system,
        "services": services,
        "connections": list(connections),
    }


async def collect_service_health(services: Dict[str, str]) -> List[Dict[str, Any]]:
    return await check_services(services)


def collect_database_health(connections: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return check_database_health_batch(connections)
