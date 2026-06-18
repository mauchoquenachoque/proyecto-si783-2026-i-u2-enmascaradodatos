import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import Body, FastAPI, HTTPException

from config import settings
from health_monitor import collect_database_health, collect_service_health
from system_metrics import collect_system_metrics

app = FastAPI(title="SecOps Monitor Service")
DB_NAME = os.path.join(settings.DATA_DIR, "monitor_metrics.db")
DEFAULT_SERVICE_URLS = {
    "api": os.getenv("API_SERVICE_URL", "http://localhost:8000"),
    "masking_service": os.getenv("MASKING_SERVICE_URL", "http://localhost:8001"),
    "monitor_service": os.getenv("MONITOR_SERVICE_URL", "http://localhost:8002"),
}

os.makedirs(settings.DATA_DIR, exist_ok=True)


def _get_conn():
    return sqlite3.connect(DB_NAME)


def _ensure_column(cursor: sqlite3.Cursor, table: str, column: str, column_type: str) -> None:
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    if column not in existing:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            motor_utilizado TEXT,
            masking_mode TEXT,
            tiempo_normal_ms REAL,
            tiempo_masked_ms REAL,
            tiempo_encrypted_ms REAL,
            latency_delta_ms REAL,
            cpu_overhead REAL,
            tiempo_bd_ms REAL,
            tiempo_mask_ms REAL,
            overhead_total_ms REAL,
            filas_procesadas INTEGER,
            timestamp TEXT
        )
    """)
    _ensure_column(cursor, "metrics", "masking_mode", "TEXT")
    _ensure_column(cursor, "metrics", "tiempo_normal_ms", "REAL")
    _ensure_column(cursor, "metrics", "tiempo_masked_ms", "REAL")
    _ensure_column(cursor, "metrics", "tiempo_encrypted_ms", "REAL")
    _ensure_column(cursor, "metrics", "latency_delta_ms", "REAL")
    _ensure_column(cursor, "metrics", "cpu_overhead", "REAL")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpu_percent REAL,
            memory_percent REAL,
            disk_percent REAL,
            uptime_seconds INTEGER,
            timestamp TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS db_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engine TEXT,
            status TEXT,
            latency_ms REAL,
            timestamp TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT,
            status TEXT,
            response_time_ms REAL,
            timestamp TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS algorithm_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            algorithm TEXT,
            columns_masked INTEGER,
            rows_processed INTEGER,
            execution_time_ms REAL,
            timestamp TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,
            error_type TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "monitor"}


@app.get("/system/metrics")
async def get_system_metrics():
    snapshot = collect_system_metrics()
    timestamp = snapshot.get("timestamp", datetime.now(timezone.utc).isoformat())
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO system_metrics (cpu_percent, memory_percent, disk_percent, uptime_seconds, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            snapshot.get("cpu_percent"),
            snapshot.get("memory_percent"),
            snapshot.get("disk_percent"),
            snapshot.get("uptime_seconds"),
            timestamp,
        ),
    )
    conn.commit()
    conn.close()
    return snapshot


@app.post("/system/metrics")
async def save_system_metrics(payload: Dict[str, Any] = Body(...)):
    timestamp = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO system_metrics (cpu_percent, memory_percent, disk_percent, uptime_seconds, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            payload.get("cpu_percent"),
            payload.get("memory_percent"),
            payload.get("disk_percent"),
            payload.get("uptime_seconds"),
            timestamp,
        ),
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


@app.post("/service-health")
async def save_service_health(payload: Dict[str, Any] = Body(default={})):
    services = payload.get("services") or DEFAULT_SERVICE_URLS
    results = await collect_service_health(services)
    timestamp = datetime.now(timezone.utc).isoformat()

    conn = _get_conn()
    cursor = conn.cursor()
    for result in results:
        cursor.execute(
            """
            INSERT INTO service_health (service_name, status, response_time_ms, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (
                result.get("service"),
                result.get("status"),
                result.get("response_time_ms"),
                timestamp,
            ),
        )
        if result.get("status") == "DOWN":
            cursor.execute(
                """
                INSERT INTO system_errors (service, error_type, message, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (
                    result.get("service"),
                    "SERVICE_DOWN",
                    f"El servicio {result.get('service')} no responde o retorno error: {result.get('error', 'Desconocido')}",
                    timestamp,
                ),
            )
    conn.commit()
    conn.close()
    return results


@app.post("/db-health")
async def save_database_health(payload: Dict[str, Any] = Body(...)):
    connections = payload.get("connections") or []
    results = collect_database_health(connections)
    conn = _get_conn()
    cursor = conn.cursor()
    for result in results:
        cursor.execute(
            """
            INSERT INTO db_health (engine, status, latency_ms, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (
                result.get("engine"),
                result.get("status"),
                result.get("latency_ms"),
                result.get("timestamp"),
            ),
        )
        if result.get("status") == "DOWN":
            cursor.execute(
                """
                INSERT INTO system_errors (service, error_type, message, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (
                    f"database_{result.get('engine')}",
                    "DATABASE_DOWN",
                    f"La base de datos {result.get('engine')} esta caida: {result.get('error', 'Desconocido')}",
                    result.get("timestamp"),
                ),
            )
    conn.commit()
    conn.close()
    return results


@app.post("/algorithm-metrics")
async def save_algorithm_metrics(payload: Dict[str, Any] = Body(...)):
    metrics = payload.get("metrics")
    if metrics is None:
        metrics = [payload]
    timestamp = datetime.now(timezone.utc).isoformat()

    conn = _get_conn()
    cursor = conn.cursor()
    rows_saved = 0
    for item in metrics:
        algorithm = item.get("algorithm")
        if not algorithm:
            continue
        cursor.execute(
            """
            INSERT INTO algorithm_metrics (algorithm, columns_masked, rows_processed, execution_time_ms, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                algorithm,
                item.get("columns_masked", 0),
                item.get("rows_processed", 0),
                item.get("execution_time_ms", 0.0),
                item.get("timestamp") or timestamp,
            ),
        )
        rows_saved += 1
    conn.commit()
    conn.close()
    return {"status": "ok", "rows_saved": rows_saved}


@app.get("/algorithm-ranking")
async def algorithm_ranking():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT algorithm,
               AVG(execution_time_ms) AS avg_ms,
               MAX(execution_time_ms) AS max_ms,
               MIN(execution_time_ms) AS min_ms,
               SUM(rows_processed) AS rows_processed,
               COUNT(*) AS samples
        FROM algorithm_metrics
        GROUP BY algorithm
        ORDER BY avg_ms ASC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    ranking = []
    for row in rows:
        ranking.append({
            "algorithm": row[0],
            "avg_ms": round(row[1], 3) if row[1] is not None else None,
            "max_ms": round(row[2], 3) if row[2] is not None else None,
            "min_ms": round(row[3], 3) if row[3] is not None else None,
            "rows_processed": row[4] or 0,
            "samples": row[5] or 0,
        })
    return ranking


@app.get("/engine-stats")
async def engine_stats():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT motor_utilizado,
               COUNT(*) AS consultas,
               AVG(tiempo_bd_ms) AS tiempo_promedio,
               MAX(tiempo_bd_ms) AS tiempo_maximo,
               AVG(overhead_total_ms) AS overhead_promedio
        FROM metrics
        WHERE motor_utilizado IS NOT NULL
        GROUP BY motor_utilizado
        ORDER BY tiempo_promedio ASC
        """
    )
    rows = cursor.fetchall()

    cursor.execute(
        """
        SELECT engine,
               SUM(CASE WHEN status = 'UP' THEN 1 ELSE 0 END) AS up_count,
               COUNT(*) AS total_count,
               AVG(latency_ms) AS avg_latency
        FROM db_health
        GROUP BY engine
        """
    )
    health_rows = cursor.fetchall()
    conn.close()

    health_lookup = {
        row[0]: {
            "up_count": row[1] or 0,
            "total_count": row[2] or 0,
            "avg_latency": round(row[3], 3) if row[3] is not None else None,
        }
        for row in health_rows
    }

    stats = []
    for row in rows:
        motor = row[0]
        availability = None
        health = health_lookup.get(motor)
        errors = None
        if health and health["total_count"]:
            availability = round((health["up_count"] / health["total_count"]) * 100, 2)
            errors = health["total_count"] - health["up_count"]
        stats.append({
            "engine": motor,
            "consultas": row[1] or 0,
            "tiempo_promedio_ms": round(row[2], 3) if row[2] is not None else None,
            "tiempo_maximo_ms": round(row[3], 3) if row[3] is not None else None,
            "overhead_promedio_ms": round(row[4], 3) if row[4] is not None else None,
            "disponibilidad_pct": availability,
            "errores": errors or 0,
            "avg_health_latency_ms": health["avg_latency"] if health else None,
        })
    return stats


@app.get("/errors")
async def get_errors(limit: int = 50):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, service, error_type, message, timestamp
        FROM system_errors
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "service": row[1],
            "error_type": row[2],
            "message": row[3],
            "timestamp": row[4],
        }
        for row in rows
    ]


@app.post("/errors")
async def save_error(payload: Dict[str, Any] = Body(...)):
    timestamp = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO system_errors (service, error_type, message, timestamp)
        VALUES (?, ?, ?, ?)
        """,
        (
            payload.get("service"),
            payload.get("error_type"),
            payload.get("message"),
            timestamp,
        ),
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


@app.post("/metrics")
async def save_metrics(payload: Dict[str, Any] = Body(...)):
    timestamp = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO metrics (
            motor_utilizado, masking_mode, tiempo_normal_ms, tiempo_masked_ms, tiempo_encrypted_ms,
            latency_delta_ms, cpu_overhead, tiempo_bd_ms, tiempo_mask_ms, overhead_total_ms,
            filas_procesadas, timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.get("motor_utilizado"),
            payload.get("masking_mode"),
            payload.get("tiempo_normal_ms"),
            payload.get("tiempo_masked_ms"),
            payload.get("tiempo_encrypted_ms"),
            payload.get("latency_delta_ms"),
            payload.get("cpu_overhead"),
            payload.get("tiempo_bd_ms"),
            payload.get("tiempo_mask_ms"),
            payload.get("overhead_total_ms"),
            payload.get("filas_procesadas"),
            timestamp,
        ),
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


@app.get("/metrics")
async def get_metrics():
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, motor_utilizado, masking_mode, tiempo_normal_ms, tiempo_masked_ms, tiempo_encrypted_ms,
                   latency_delta_ms, cpu_overhead, tiempo_bd_ms, tiempo_mask_ms, overhead_total_ms,
                   filas_procesadas, timestamp
            FROM metrics
            ORDER BY id DESC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        metrics = []
        for r in rows:
            metrics.append({
                "id": r[0],
                "motor_utilizado": r[1],
                "masking_mode": r[2],
                "tiempo_normal_ms": r[3],
                "tiempo_masked_ms": r[4],
                "tiempo_encrypted_ms": r[5],
                "latency_delta_ms": r[6],
                "cpu_overhead": r[7],
                "tiempo_bd_ms": r[8],
                "tiempo_mask_ms": r[9],
                "overhead_total_ms": r[10],
                "filas_procesadas": r[11],
                "timestamp": r[12]
            })
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("monitor_service:app", host="0.0.0.0", port=8002)
