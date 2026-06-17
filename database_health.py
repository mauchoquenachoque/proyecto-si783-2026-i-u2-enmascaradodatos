import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from database_manager import DatabaseFactory


def _get_engine_query(motor_nombre: str) -> tuple[Any, Dict[str, Any]]:
    motor = motor_nombre.lower()
    if motor in {"postgres", "mysql", "sqlserver", "sqlite"}:
        if motor == "sqlserver":
            return "SELECT 1", {}
        return "SELECT 1", {}
    if motor == "mongodb":
        return {"ping": 1}, {}
    if motor == "redis":
        return "ping", {"tipo_comando": "ping"}
    if motor == "neo4j":
        return "RETURN 1 AS ok", {"parametros": {}}
    return "SELECT 1", {}


def check_database_health(motor_nombre: str, credenciales: Dict[str, Any]) -> Dict[str, Any]:
    started = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        motor = DatabaseFactory.obtener_motor(motor_nombre, credenciales)
        query, kwargs = _get_engine_query(motor_nombre)

        if motor_nombre.lower() == "mongodb":
            cliente = motor.conectar()
            try:
                cliente.admin.command("ping")
            finally:
                cliente.close()
        elif motor_nombre.lower() == "redis":
            cliente = motor.conectar()
            try:
                cliente.ping()
            finally:
                cliente.close()
        elif motor_nombre.lower() == "neo4j":
            driver = motor.conectar()
            try:
                with driver.session() as session:
                    session.run(query)
            finally:
                driver.close()
        else:
            motor.ejecutar_consulta(query, **kwargs)

        status = "UP"
        error_message = None
    except Exception as exc:
        status = "DOWN"
        error_message = str(exc)
    latency_ms = round((time.perf_counter() - started) * 1000, 3)

    result = {
        "engine": motor_nombre,
        "status": status,
        "latency_ms": latency_ms,
        "timestamp": timestamp,
    }
    if error_message:
        result["error"] = error_message
    return result


def check_database_health_batch(connections: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for connection in connections:
        motor_nombre = connection.get("motor") or connection.get("motor_nombre")
        credenciales = connection.get("credenciales") or {}
        alias = connection.get("alias")
        result = check_database_health(motor_nombre, credenciales)
        if alias:
            result["alias"] = alias
        results.append(result)
    return results
