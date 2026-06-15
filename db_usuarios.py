"""
db_usuarios.py — Gestión de la tabla usuarios_plataforma
Base de datos SQLite interna del sistema SecOps.

Contiene:
- Inicialización del esquema
- Registro con hash bcrypt (local) o sin contraseña (Google)
- Autenticación por email + password
- Auto-creación del usuario administrador por defecto
"""

import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from passlib.context import CryptContext

from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PLATFORM_DB = os.path.join(settings.DATA_DIR, "platform_users.db")

ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL", "admin@secops.local")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin1234!")
ADMIN_NAME     = os.getenv("ADMIN_NAME", "Administrador SecOps")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(PLATFORM_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea la tabla de usuarios si no existe y siembra el admin por defecto."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios_plataforma (
                id              TEXT PRIMARY KEY,
                nombre_completo TEXT NOT NULL,
                correo          TEXT UNIQUE NOT NULL,
                password_hash   TEXT,
                proveedor       TEXT NOT NULL DEFAULT 'local',
                google_id       TEXT,
                foto_url        TEXT,
                fecha_registro  TEXT NOT NULL
            )
        """)
        # Migración: agregar columnas si no existen
        try:
            conn.execute("ALTER TABLE usuarios_plataforma ADD COLUMN google_id TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE usuarios_plataforma ADD COLUMN foto_url TEXT")
        except Exception:
            pass
        conn.commit()

    if not buscar_usuario_por_correo(ADMIN_EMAIL):
        registrar_usuario(ADMIN_NAME, ADMIN_EMAIL, ADMIN_PASSWORD, proveedor="local")
        print(f"[DB_USUARIOS] Usuario administrador creado: {ADMIN_EMAIL}")
    else:
        print(f"[DB_USUARIOS] Tabla usuarios_plataforma OK. Admin: {ADMIN_EMAIL}")


def registrar_usuario(
    nombre: str,
    correo: str,
    password: str = "",
    proveedor: str = "local",
    google_id: str = None,
    foto_url: str = None,
) -> Dict[str, Any]:
    """
    Inserta un nuevo usuario.
    - local: requiere password (bcrypt hash)
    - google: password vacío, requiere google_id
    """
    if proveedor == "local" and not password:
        raise ValueError("La contraseña es obligatoria para registro local.")
    
    if buscar_usuario_por_correo(correo):
        # Si ya existe y es login de Google, retornar el existente
        existente = buscar_usuario_por_correo(correo)
        if proveedor == "google":
            return {
                "id": existente["id"],
                "nombre": existente["nombre_completo"],
                "correo": existente["correo"],
                "proveedor": existente["proveedor"]
            }
        raise ValueError(f"El correo '{correo}' ya está registrado.")

    usuario_id = str(uuid.uuid4())
    hash_pwd = pwd_context.hash(password) if password else None
    fecha = datetime.now(timezone.utc).isoformat()

    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO usuarios_plataforma (id, nombre_completo, correo, password_hash, proveedor, google_id, foto_url, fecha_registro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (usuario_id, nombre, correo, hash_pwd, proveedor, google_id, foto_url, fecha)
        )
        conn.commit()

    return {"id": usuario_id, "nombre": nombre, "correo": correo, "proveedor": proveedor}


def autenticar_usuario(correo: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Valida email + contraseña. Retorna el usuario si OK, None si falla.
    """
    usuario = buscar_usuario_por_correo(correo)
    if not usuario:
        return None
    if not usuario["password_hash"]:
        return None  # Usuario de Google, no tiene password
    if not pwd_context.verify(password, usuario["password_hash"]):
        return None
    return dict(usuario)


def buscar_usuario_por_correo(correo: str) -> Optional[sqlite3.Row]:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM usuarios_plataforma WHERE correo = ?", (correo,)
        ).fetchone()
    return row


def actualizar_usuario_google(correo: str, google_id: str, foto_url: str = None) -> None:
    """Actualiza los datos de Google de un usuario existente."""
    with _get_conn() as conn:
        conn.execute(
            "UPDATE usuarios_plataforma SET google_id = ?, foto_url = ? WHERE correo = ?",
            (google_id, foto_url, correo)
        )
        conn.commit()
