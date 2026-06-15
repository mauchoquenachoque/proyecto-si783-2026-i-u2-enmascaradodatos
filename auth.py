"""
auth.py — Gestión de sesiones persistente con SQLite
Las sesiones sobreviven reinicios del servidor (Render free tier cold starts).
"""

import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from fastapi import Request, HTTPException, status
from typing import Dict, Any, Optional

from config import settings

# Archivo SQLite exclusivo para sesiones
SESSIONS_DB = os.path.join(settings.DATA_DIR, "sessions.db")

# Cache en memoria para rendimiento (se reconstruye desde SQLite si se pierde)
_cache_sesiones: Dict[str, Dict[str, Any]] = {}


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(SESSIONS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_sessions_db():
    """Crea la tabla de sesiones si no existe."""
    try:
        with _get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sesiones (
                    token       TEXT PRIMARY KEY,
                    username    TEXT NOT NULL,
                    email       TEXT NOT NULL,
                    proveedor   TEXT NOT NULL DEFAULT 'local',
                    conexiones  TEXT NOT NULL DEFAULT '{}',
                    created_at  TEXT NOT NULL,
                    last_access TEXT NOT NULL
                )
            """)
            conn.commit()
        print("[AUTH] Tabla de sesiones OK")
    except Exception as e:
        print(f"[AUTH] Error creando tabla sesiones: {e}")


# Inicializar al importar
init_sessions_db()


def _cargar_sesiones_en_cache():
    """Carga todas las sesiones activas desde SQLite a memoria."""
    global _cache_sesiones
    try:
        with _get_conn() as conn:
            rows = conn.execute("SELECT * FROM sesiones").fetchall()
            _cache_sesiones = {}
            for row in rows:
                import json
                conexiones = json.loads(row["conexiones"]) if row["conexiones"] else {}
                _cache_sesiones[row["token"]] = {
                    "username": row["username"],
                    "email": row["email"],
                    "proveedor": row["proveedor"],
                    "conexiones": conexiones
                }
        print(f"[AUTH] {len(_cache_sesiones)} sesiones cargadas desde SQLite")
    except Exception as e:
        print(f"[AUTH] Error cargando sesiones: {e}")
        _cache_sesiones = {}


# Cargar sesiones existentes al arrancar
_cargar_sesiones_en_cache()


def crear_token_sesion(username: str, email: str, proveedor: str = "local") -> str:
    """Genera un token seguro y registra la sesión en SQLite + caché."""
    token = secrets.token_hex(32)
    ahora = datetime.now(timezone.utc).isoformat()

    sesion_data = {
        "username": username,
        "email": email,
        "proveedor": proveedor,
        "conexiones": {}
    }

    # Guardar en SQLite
    try:
        import json
        with _get_conn() as conn:
            conn.execute("""
                INSERT INTO sesiones (token, username, email, proveedor, conexiones, created_at, last_access)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (token, username, email, proveedor, json.dumps({}), ahora, ahora))
            conn.commit()
    except Exception as e:
        print(f"[AUTH] Error guardando sesión en SQLite: {e}")

    # Guardar en caché
    _cache_sesiones[token] = sesion_data
    return token


def revocar_token(token: str):
    """Elimina la sesión de SQLite y caché."""
    # Eliminar de SQLite
    try:
        with _get_conn() as conn:
            conn.execute("DELETE FROM sesiones WHERE token = ?", (token,))
            conn.commit()
    except Exception as e:
        print(f"[AUTH] Error eliminando sesión de SQLite: {e}")

    # Eliminar de caché
    _cache_sesiones.pop(token, None)


def obtener_sesion_actual(request: Request) -> Dict[str, Any]:
    """Extrae y valida la sesión desde la cookie HTTP-only."""
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autorizado. Inicia sesión.",
        )

    # Buscar en caché primero
    sesion = _cache_sesiones.get(token)
    if sesion:
        # Actualizar last_access en background
        _actualizar_last_access(token)
        return sesion

    # Si no está en caché, buscar en SQLite (posible reinicio del servidor)
    sesion = _cargar_sesion_desde_db(token)
    if sesion:
        _cache_sesiones[token] = sesion
        _actualizar_last_access(token)
        return sesion

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesión expirada o inválida. Inicia sesión nuevamente.",
    )


def _cargar_sesion_desde_db(token: str) -> Optional[Dict[str, Any]]:
    """Carga una sesión específica desde SQLite."""
    try:
        import json
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM sesiones WHERE token = ?", (token,)
            ).fetchone()
            if row:
                conexiones = json.loads(row["conexiones"]) if row["conexiones"] else {}
                return {
                    "username": row["username"],
                    "email": row["email"],
                    "proveedor": row["proveedor"],
                    "conexiones": conexiones
                }
    except Exception as e:
        print(f"[AUTH] Error cargando sesión desde DB: {e}")
    return None


def _actualizar_last_access(token: str):
    """Actualiza el timestamp de último acceso (sin bloquear)."""
    try:
        ahora = datetime.now(timezone.utc).isoformat()
        with _get_conn() as conn:
            conn.execute(
                "UPDATE sesiones SET last_access = ? WHERE token = ?",
                (ahora, token)
            )
            conn.commit()
    except Exception:
        pass


def _persistir_conexiones(token: str):
    """Guarda el mapa de conexiones actual en SQLite."""
    try:
        import json
        sesion = _cache_sesiones.get(token)
        if sesion:
            with _get_conn() as conn:
                conn.execute(
                    "UPDATE sesiones SET conexiones = ? WHERE token = ?",
                    (json.dumps(sesion.get("conexiones", {})), token)
                )
                conn.commit()
    except Exception as e:
        print(f"[AUTH] Error persistiendo conexiones: {e}")


# ── Conexiones concurrentes ───────────────────────────────────────────────────

def agregar_conexion(request: Request, config: Dict[str, Any]) -> str:
    token = request.cookies.get("session_token")
    if token and token in _cache_sesiones:
        conn_id = uuid.uuid4().hex
        _cache_sesiones[token]["conexiones"][conn_id] = config
        _persistir_conexiones(token)
        return conn_id
    raise HTTPException(status_code=401, detail="Sesión inválida")


def obtener_conexion(request: Request, connection_id: str) -> Dict[str, Any]:
    sesion = obtener_sesion_actual(request)
    conexiones = sesion.get("conexiones", {})
    if connection_id not in conexiones:
        raise HTTPException(status_code=404, detail="Conexión no encontrada o expirada.")
    return conexiones[connection_id]


def eliminar_conexion(request: Request, connection_id: str):
    token = request.cookies.get("session_token")
    if token and token in _cache_sesiones:
        _cache_sesiones[token]["conexiones"].pop(connection_id, None)
        _persistir_conexiones(token)


def limpiar_sesiones_expiradas(dias: int = 7):
    """Elimina sesiones más antiguas que N días."""
    try:
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()
        with _get_conn() as conn:
            result = conn.execute(
                "DELETE FROM sesiones WHERE last_access < ?", (cutoff,)
            )
            conn.commit()
            if result.rowcount > 0:
                print(f"[AUTH] {result.rowcount} sesiones expiradas eliminadas")
    except Exception as e:
        print(f"[AUTH] Error limpiando sesiones: {e}")


def obtener_estadisticas_sesiones() -> Dict[str, Any]:
    """Retorna estadísticas de sesiones para el dashboard."""
    try:
        with _get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM sesiones").fetchone()[0]
            activas = len(_cache_sesiones)
            return {
                "total_en_db": total,
                "en_cache": activas,
                "status": "ok"
            }
    except Exception as e:
        return {"total_en_db": 0, "en_cache": 0, "status": "error", "detail": str(e)}
