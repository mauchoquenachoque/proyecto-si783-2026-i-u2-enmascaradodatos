"""
health_monitor.py — Monitor de Salud de Bases de Datos
Endpoint que verifica la conectividad con todas las BDs configuradas
y genera un reporte detallado de estado.
"""

import os
import time
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config import settings

# Archivo para historial de health checks
HEALTH_DB = os.path.join(settings.DATA_DIR, "health_monitor.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(HEALTH_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_health_db():
    """Crea la tabla de historial de health checks."""
    try:
        with _get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS health_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    servicio TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    latencia_ms REAL,
                    detalle TEXT
                )
            """)
            conn.commit()
        print("[HEALTH] Tabla de historial OK")
    except Exception as e:
        print(f"[HEALTH] Error creando tabla: {e}")


init_health_db()


async def verificar_postgres() -> Dict[str, Any]:
    """Verifica conectividad con PostgreSQL."""
    inicio = time.perf_counter()
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=settings.PG_HOST,
            port=settings.PG_PORT,
            user=settings.PG_USER,
            password=settings.PG_PASSWORD,
            dbname=settings.PG_DB,
            connect_timeout=5
        )
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
        tablas = cur.fetchone()[0]
        conn.close()
        latencia = (time.perf_counter() - inicio) * 1000
        return {
            "servicio": "PostgreSQL",
            "estado": "OK",
            "latencia_ms": round(latencia, 2),
            "version": version,
            "tablas": tablas,
            "host": settings.PG_HOST,
            "detalle": None
        }
    except Exception as e:
        latencia = (time.perf_counter() - inicio) * 1000
        return {
            "servicio": "PostgreSQL",
            "estado": "ERROR",
            "latencia_ms": round(latencia, 2),
            "version": None,
            "tablas": 0,
            "host": settings.PG_HOST,
            "detalle": str(e)
        }


async def verificar_mysql() -> Dict[str, Any]:
    """Verifica conectividad con MySQL."""
    inicio = time.perf_counter()
    try:
        import pymysql
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DB,
            connect_timeout=5
        )
        cur = conn.cursor()
        cur.execute("SELECT VERSION()")
        version = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s", (settings.MYSQL_DB,))
        tablas = cur.fetchone()[0]
        conn.close()
        latencia = (time.perf_counter() - inicio) * 1000
        return {
            "servicio": "MySQL",
            "estado": "OK",
            "latencia_ms": round(latencia, 2),
            "version": version,
            "tablas": tablas,
            "host": settings.MYSQL_HOST,
            "detalle": None
        }
    except Exception as e:
        latencia = (time.perf_counter() - inicio) * 1000
        return {
            "servicio": "MySQL",
            "estado": "ERROR",
            "latencia_ms": round(latencia, 2),
            "version": None,
            "tablas": 0,
            "host": settings.MYSQL_HOST,
            "detalle": str(e)
        }


async def verificar_sqlserver() -> Dict[str, Any]:
    """Verifica conectividad con SQL Server."""
    inicio = time.perf_counter()
    try:
        import pymssql
        conn = pymssql.connect(
            server=settings.MSSQL_HOST,
            port=str(settings.MSSQL_PORT),
            user=settings.MSSQL_USER,
            password=settings.MSSQL_PASSWORD,
            database=settings.MSSQL_DB,
            login_timeout=5
        )
        cur = conn.cursor(as_dict=True)
        cur.execute("SELECT @@VERSION AS version")
        version = cur.fetchone()["version"][:80]
        cur.execute("SELECT COUNT(*) AS cnt FROM INFORMATION_SCHEMA.TABLES")
        tablas = cur.fetchone()["cnt"]
        conn.close()
        latencia = (time.perf_counter() - inicio) * 1000
        return {
            "servicio": "SQL Server",
            "estado": "OK",
            "latencia_ms": round(latencia, 2),
            "version": version,
            "tablas": tablas,
            "host": settings.MSSQL_HOST,
            "detalle": None
        }
    except Exception as e:
        latencia = (time.perf_counter() - inicio) * 1000
        return {
            "servicio": "SQL Server",
            "estado": "ERROR",
            "latencia_ms": round(latencia, 2),
            "version": None,
            "tablas": 0,
            "host": settings.MSSQL_HOST,
            "detalle": str(e)
        }


async def verificar_mongodb() -> Dict[str, Any]:
    """Verifica conectividad con MongoDB."""
    inicio = time.perf_counter()
    try:
        from pymongo import MongoClient
        client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[settings.MONGO_DB]
        # Ping
        client.admin.command('ping')
        # Info
        server_info = client.server_info()
        version = server_info.get("version", "unknown")
        colecciones = len(db.list_collection_names())
        client.close()
        latencia = (time.perf_counter() - inicio) * 1000
        return {
            "servicio": "MongoDB",
            "estado": "OK",
            "latencia_ms": round(latencia, 2),
            "version": version,
            "tablas": colecciones,
            "host": settings.MONGO_URI,
            "detalle": None
        }
    except Exception as e:
        latencia = (time.perf_counter() - inicio) * 1000
        return {
            "servicio": "MongoDB",
            "estado": "ERROR",
            "latencia_ms": round(latencia, 2),
            "version": None,
            "tablas": 0,
            "host": settings.MONGO_URI,
            "detalle": str(e)
        }


async def verificar_redis() -> Dict[str, Any]:
    """Verifica conectividad con Redis."""
    inicio = time.perf_counter()
    try:
        import redis
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            socket_timeout=5,
            decode_responses=True
        )
        info = r.info("server")
        version = info.get("redis_version", "unknown")
        keys = r.dbsize()
        r.close()
        latencia = (time.perf_counter() - inicio) * 1000
        return {
            "servicio": "Redis",
            "estado": "OK",
            "latencia_ms": round(latencia, 2),
            "version": version,
            "tablas": keys,
            "host": settings.REDIS_HOST,
            "detalle": None
        }
    except Exception as e:
        latencia = (time.perf_counter() - inicio) * 1000
        return {
            "servicio": "Redis",
            "estado": "ERROR",
            "latencia_ms": round(latencia, 2),
            "version": None,
            "tablas": 0,
            "host": settings.REDIS_HOST,
            "detalle": str(e)
        }


async def verificar_neo4j() -> Dict[str, Any]:
    """Verifica conectividad con Neo4j."""
    inicio = time.perf_counter()
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            connection_timeout=5
        )
        with driver.session() as session:
            result = session.run("CALL dbms.components() YIELD versions RETURN versions[0] AS version")
            version = result.single()["version"]
            result = session.run("MATCH (n) RETURN count(n) AS count")
            nodos = result.single()["count"]
        driver.close()
        latencia = (time.perf_counter() - inicio) * 1000
        return {
            "servicio": "Neo4j",
            "estado": "OK",
            "latencia_ms": round(latencia, 2),
            "version": version,
            "tablas": nodos,
            "host": settings.NEO4J_URI,
            "detalle": None
        }
    except Exception as e:
        latencia = (time.perf_counter() - inicio) * 1000
        return {
            "servicio": "Neo4j",
            "estado": "ERROR",
            "latencia_ms": round(latencia, 2),
            "version": None,
            "tablas": 0,
            "host": settings.NEO4J_URI,
            "detalle": str(e)
        }


async def verificar_sqlite_interno() -> Dict[str, Any]:
    """Verifica las bases de datos SQLite internas del sistema."""
    inicio = time.perf_counter()
    dbs = ["platform_users.db", "sessions.db", "health_monitor.db"]
    resultados = []
    
    for db_name in dbs:
        db_path = os.path.join(settings.DATA_DIR, db_name)
        try:
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path, timeout=5)
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                tablas = cur.fetchone()[0]
                size = os.path.getsize(db_path)
                conn.close()
                resultados.append({
                    "archivo": db_name,
                    "estado": "OK",
                    "tablas": tablas,
                    "tamaño_kb": round(size / 1024, 2)
                })
            else:
                resultados.append({
                    "archivo": db_name,
                    "estado": "NO_EXISTE",
                    "tablas": 0,
                    "tamaño_kb": 0
                })
        except Exception as e:
            resultados.append({
                "archivo": db_name,
                "estado": "ERROR",
                "tablas": 0,
                "tamaño_kb": 0,
                "detalle": str(e)
            })
    
    latencia = (time.perf_counter() - inicio) * 1000
    ok_count = sum(1 for r in resultados if r["estado"] == "OK")
    
    return {
        "servicio": "SQLite Interno",
        "estado": "OK" if ok_count == len(dbs) else "DEGRADADO",
        "latencia_ms": round(latencia, 2),
        "version": sqlite3.sqlite_version,
        "tablas": sum(r["tablas"] for r in resultados),
        "host": "local",
        "detalle": None,
        "bases_datos": resultados
    }


async def verificar_servicios_secops() -> Dict[str, Any]:
    """Verifica los microservicios de SecOps (Masking y Monitor)."""
    import httpx
    
    resultados = []
    
    # Masking Service
    inicio = time.perf_counter()
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{settings.MASKING_SERVICE_URL}/health", timeout=5)
            latencia = (time.perf_counter() - inicio) * 1000
            if res.status_code == 200:
                resultados.append({
                    "servicio": "Masking Service",
                    "estado": "OK",
                    "latencia_ms": round(latencia, 2),
                    "detalle": None
                })
            else:
                resultados.append({
                    "servicio": "Masking Service",
                    "estado": "ERROR",
                    "latencia_ms": round(latencia, 2),
                    "detalle": f"HTTP {res.status_code}"
                })
    except Exception as e:
        latencia = (time.perf_counter() - inicio) * 1000
        resultados.append({
            "servicio": "Masking Service",
            "estado": "ERROR",
            "latencia_ms": round(latencia, 2),
            "detalle": str(e)
        })
    
    # Monitor Service
    inicio = time.perf_counter()
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{settings.MONITOR_SERVICE_URL}/health", timeout=5)
            latencia = (time.perf_counter() - inicio) * 1000
            if res.status_code == 200:
                resultados.append({
                    "servicio": "Monitor Service",
                    "estado": "OK",
                    "latencia_ms": round(latencia, 2),
                    "detalle": None
                })
            else:
                resultados.append({
                    "servicio": "Monitor Service",
                    "estado": "ERROR",
                    "latencia_ms": round(latencia, 2),
                    "detalle": f"HTTP {res.status_code}"
                })
    except Exception as e:
        latencia = (time.perf_counter() - inicio) * 1000
        resultados.append({
            "servicio": "Monitor Service",
            "estado": "ERROR",
            "latencia_ms": round(latencia, 2),
            "detalle": str(e)
        })
    
    return resultados


async def ejecutar_health_check_completo() -> Dict[str, Any]:
    """
    Ejecuta un health check completo de todas las bases de datos y servicios.
    Retorna un reporte detallado con estado, latencia y versiones.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Verificar BDs externas (en paralelo sería ideal, pero mantenemos simplicidad)
    checks_bd = []
    
    # Solo verificar BDs que tienen configuración válida
    if settings.PG_HOST and settings.PG_HOST != "localhost":
        checks_bd.append(await verificar_postgres())
    
    if settings.MYSQL_HOST and settings.MYSQL_HOST != "localhost":
        checks_bd.append(await verificar_mysql())
    
    if settings.MSSQL_HOST and settings.MSSQL_HOST != "localhost":
        checks_bd.append(await verificar_sqlserver())
    
    if settings.MONGO_URI and "localhost" not in settings.MONGO_URI:
        checks_bd.append(await verificar_mongodb())
    
    if settings.REDIS_HOST and settings.REDIS_HOST != "localhost":
        checks_bd.append(await verificar_redis())
    
    if settings.NEO4J_URI and "localhost" not in settings.NEO4J_URI:
        checks_bd.append(await verificar_neo4j())
    
    # Siempre verificar SQLite interno
    sqlite_check = await verificar_sqlite_interno()
    checks_bd.append(sqlite_check)
    
    # Verificar servicios SecOps
    servicios_checks = await verificar_servicios_secops()
    
    # Calcular resumen
    total = len(checks_bd) + len(servicios_checks)
    ok = sum(1 for c in checks_bd if c.get("estado") == "OK") + sum(1 for c in servicios_checks if c.get("estado") == "OK")
    errores = total - ok
    
    # Guardar en historial
    try:
        with _get_conn() as conn:
            for check in checks_bd + servicios_checks:
                conn.execute("""
                    INSERT INTO health_history (timestamp, servicio, estado, latencia_ms, detalle)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    check.get("servicio", "unknown"),
                    check.get("estado", "UNKNOWN"),
                    check.get("latencia_ms", 0),
                    check.get("detalle")
                ))
            conn.commit()
    except Exception:
        pass
    
    return {
        "timestamp": timestamp,
        "resumen": {
            "total": total,
            "ok": ok,
            "errores": errores,
            "estado_general": "SALUDABLE" if errores == 0 else "DEGRADADO" if ok > 0 else "CAIDO"
        },
        "bases_datos": checks_bd,
        "servicios": servicios_checks
    }


async def obtener_historial_health(servicio: Optional[str] = None, limite: int = 50) -> List[Dict[str, Any]]:
    """Obtiene el historial de health checks."""
    try:
        with _get_conn() as conn:
            if servicio:
                rows = conn.execute("""
                    SELECT * FROM health_history 
                    WHERE servicio = ? 
                    ORDER BY id DESC LIMIT ?
                """, (servicio, limite)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM health_history 
                    ORDER BY id DESC LIMIT ?
                """, (limite,)).fetchall()
            
            return [dict(row) for row in rows]
    except Exception:
        return []


async def obtener_estadisticas_salud() -> Dict[str, Any]:
    """Retorna estadísticas agregadas de salud."""
    try:
        with _get_conn() as conn:
            # Últimas 24 horas
            rows = conn.execute("""
                SELECT servicio, estado, COUNT(*) as cnt, AVG(latencia_ms) as latencia_avg
                FROM health_history
                WHERE timestamp > datetime('now', '-1 day')
                GROUP BY servicio, estado
            """).fetchall()
            
            stats = {}
            for row in rows:
                servicio = row["servicio"]
                if servicio not in stats:
                    stats[servicio] = {"ok": 0, "error": 0, "latencia_avg": 0}
                if row["estado"] == "OK":
                    stats[servicio]["ok"] = row["cnt"]
                else:
                    stats[servicio]["error"] = row["cnt"]
                stats[servicio]["latencia_avg"] = round(row["latencia_avg"], 2)
            
            return stats
    except Exception:
        return {}
