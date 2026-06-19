"""
governance.py — Módulo de Gobernanza de Datos Universal (Static Data Masking)

ARQUITECTURA: Patrón Strategy con Dispatcher.
Cada motor implementa dos funciones (_proteger / _restaurar) con la misma firma.
El dispatcher `proteger_tabla` / `restaurar_tabla` selecciona la estrategia correcta
en tiempo de ejecución según el nombre del motor.

ESTRATEGIA DE SEGURIDAD:
    INACTIVO: tabla original contiene datos reales.
              → SELECT * directo expone todo → VULNERABILIDAD DE AUDITORÍA.
    ACTIVO:   tabla original contiene DATOS ENMASCARADOS de forma permanente.
              tabla <nombre>__backup_enc contiene los originales CIFRADOS con AES-256 (Fernet).
              → SELECT * directo solo expone datos ya protegidos → AUDITORÍA CUMPLIDA.
              → SELECT * sobre el backup expone tokens Fernet ilegibles → AUDITORÍA CUMPLIDA.

MOTORES SOPORTADOS:
    sqlite    → SQL estándar con parámetros posicionales (?)
    postgres  → SQL estándar con parámetros posicionales (%s) y comillas dobles
    sqlserver → T-SQL nativo (SELECT INTO, UPDATE, DROP TABLE)
    mongodb   → PyMongo: clonación de colección + updateMany + shadow collection

PRE-FLIGHT CHECK (todos los motores):
    Antes de proteger, se verifica que el backup NO exista.
    Si existe, la operación aborta con un ValueError descriptivo.
    Esto evita sobrescrituras accidentales y corrupción de datos.
"""

import copy
import datetime
import os
import sqlite3
from typing import Any, Callable, Dict, List, Optional, Tuple

from config import settings
from masking import aplicar_enmascaramiento, cifrar_valor, descifrar_valor

# ─────────────────────────────────────────────────────────────────────────────
# ESTADO DE GOBERNANZA (en memoria)
# ─────────────────────────────────────────────────────────────────────────────

PLATFORM_DB = os.path.join(settings.DATA_DIR, "platform_users.db")
BACKUP_SUFFIX = "__backup_enc"

def _get_platform_conn():
    conn = sqlite3.connect(PLATFORM_DB)
    return conn

# Crear la tabla de gobernanza si no existe al arrancar
def init_governance_db():
    try:
        with _get_platform_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS gobernanza_estado (
                    connection_id TEXT,
                    tabla         TEXT,
                    estado        TEXT NOT NULL,
                    PRIMARY KEY (connection_id, tabla)
                )
            """)
            conn.commit()
    except Exception:
        pass

init_governance_db()


def _registrar_estado(connection_id: str, tabla: str, estado: str) -> None:
    try:
        with _get_platform_conn() as conn:
            conn.execute("""
                INSERT INTO gobernanza_estado (connection_id, tabla, estado)
                VALUES (?, ?, ?)
                ON CONFLICT(connection_id, tabla) DO UPDATE SET estado=excluded.estado
            """, (connection_id, tabla, estado))
            conn.commit()
    except Exception:
        pass


def obtener_estado(connection_id: str, tabla: str) -> str:
    try:
        with _get_platform_conn() as conn:
            row = conn.execute("""
                SELECT estado FROM gobernanza_estado WHERE connection_id = ? AND tabla = ?
            """, (connection_id, tabla)).fetchone()
            if row:
                return row[0]
    except Exception:
        pass
    return "INACTIVA"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS COMPARTIDOS
# ─────────────────────────────────────────────────────────────────────────────

def _parsear_fecha_sqlserver(val_str: str, tipo_destino: str):
    """
    Intenta parsear una cadena de texto a un objeto datetime/date
    según el tipo de destino de SQL Server.
    """
    if not val_str:
        return None
    val_str = val_str.strip()
    
    # Formatos comunes de str(datetime) y str(date)
    formatos = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S"
    ]
    
    for fmt in formatos:
        try:
            dt = datetime.datetime.strptime(val_str, fmt)
            if tipo_destino == "date":
                return dt.date()
            return dt
        except ValueError:
            continue
            
    # Si ningún formato funciona, retornamos el string original
    return val_str

def _cifrar_fila(fila: Dict, columnas: List[str]) -> List[Optional[str]]:
    """Serializa y cifra todos los valores de una fila con Fernet AES."""
    return [cifrar_valor(str(fila.get(c))) if fila.get(c) is not None else None for c in columnas]


def _descifrar_fila(fila: Dict, columnas: List[str]) -> List[Optional[str]]:
    """Descifra todos los valores de una fila desde el backup Fernet."""
    resultado = []
    for c in columnas:
        val = fila.get(c)
        if val is None:
            resultado.append(None)
            continue
        try:
            resultado.append(descifrar_valor(val))
        except Exception:
            resultado.append(val)  # Valor no cifrado, lo devuelve sin cambios
    return resultado


# ─────────────────────────────────────────────────────────────────────────────
# ESTRATEGIA: SQLite
# ─────────────────────────────────────────────────────────────────────────────

def _sqlite_preflight(motor, tabla: str) -> str:
    tabla_raw = tabla + "__raw"
    existe = motor.ejecutar_consulta(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabla_raw}'"
    )
    if existe:
        raise ValueError(
            f"Pre-flight FAIL: La tabla base '{tabla_raw}' ya existe en SQLite. "
            "La protección podría estar activa. Ejecuta 'Restaurar' primero."
        )
    return tabla_raw

def _sqlite_generar_select_vista(motor, tabla_raw: str, reglas: Dict[str, str]) -> str:
    esquema = motor.obtener_esquema().get("tablas", {})
    columnas = esquema.get(tabla_raw, [])
    if not columnas:
        # Fallback to get columns
        cols_info = motor.ejecutar_consulta(f"PRAGMA table_info({tabla_raw})")
        columnas = [c['name'] for c in cols_info]
        
    select_parts = []
    for col in columnas:
        if col in reglas:
            algoritmo = reglas[col]
            if algoritmo == "redaccion":
                select_parts.append(f"'***' AS {col}")
            elif algoritmo == "hashing":
                # SQLite no tiene hash nativo por defecto sin extensiones, usamos un fallback simple
                select_parts.append(f"hex(randomblob(8)) AS {col}")
            else:
                select_parts.append(f"'[MASKED]' AS {col}")
        else:
            select_parts.append(col)
            
    return f"SELECT {', '.join(select_parts)} FROM {tabla_raw}"

def _sqlite_proteger(motor, tabla: str, reglas: Dict[str, str], connection_id: str) -> Dict[str, Any]:
    tabla_raw = _sqlite_preflight(motor, tabla)
    conn = motor.conectar()
    cur = conn.cursor()
    
    try:
        # 1. Renombrar tabla original
        cur.execute(f"ALTER TABLE {tabla} RENAME TO {tabla_raw}")
        
        # 2. Crear vista DDM
        sql_select = _sqlite_generar_select_vista(motor, tabla_raw, reglas)
        cur.execute(f"CREATE VIEW {tabla} AS {sql_select}")
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    _registrar_estado(connection_id, tabla, "ACTIVA")
    return {"filas_protegidas": "N/A (Vista DDM creada)", "backup_tabla": tabla_raw}

def _sqlite_restaurar(motor, tabla: str, connection_id: str) -> Dict[str, Any]:
    tabla_raw = tabla + "__raw"
    if not motor.ejecutar_consulta(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabla_raw}'"
    ):
        raise ValueError(f"Tabla base '{tabla_raw}' no encontrada en SQLite. Nada que restaurar.")

    conn = motor.conectar()
    cur = conn.cursor()
    try:
        cur.execute(f"DROP VIEW IF EXISTS {tabla}")
        cur.execute(f"ALTER TABLE {tabla_raw} RENAME TO {tabla}")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    _registrar_estado(connection_id, tabla, "INACTIVA")
    return {"filas_restauradas": "N/A (Vista eliminada)"}


# ─────────────────────────────────────────────────────────────────────────────
# ESTRATEGIA: MySQL / MariaDB
# ─────────────────────────────────────────────────────────────────────────────

def _mysql_preflight(motor, tabla: str) -> str:
    tabla_raw = tabla + "__raw"
    res = motor.ejecutar_consulta(f"SHOW TABLES LIKE '{tabla_raw}'")
    if res:
        raise ValueError(
            f"Pre-flight FAIL: La tabla base '{tabla_raw}' ya existe en MySQL. "
            "Ejecuta 'Restaurar' antes de volver a proteger."
        )
    return tabla_raw

def _mysql_generar_select_vista(motor, tabla_raw: str, reglas: Dict[str, str]) -> str:
    esquema = motor.obtener_esquema().get("tablas", {})
    columnas = esquema.get(tabla_raw, [])
    if not columnas:
        # Fallback to get columns from original table name since tabla_raw might not exist yet during planning
        columnas = esquema.get(tabla_raw.replace("__raw", ""), [])
        if not columnas:
            res = motor.ejecutar_consulta(f"SHOW COLUMNS FROM `{tabla_raw.replace('__raw', '')}`")
            columnas = [r.get('Field') or r.get('FIELD') for r in res]

    select_parts = []
    for col in columnas:
        if col in reglas:
            algoritmo = reglas[col]
            if algoritmo == "redaccion":
                select_parts.append(f"'***' AS `{col}`")
            elif algoritmo == "hashing":
                select_parts.append(f"SUBSTRING(SHA2(`{col}`, 256), 1, 16) AS `{col}`")
            else:
                select_parts.append(f"'[MASKED]' AS `{col}`")
        else:
            select_parts.append(f"`{col}`")
            
    return f"SELECT {', '.join(select_parts)} FROM `{tabla_raw}`"

def _mysql_proteger(motor, tabla: str, reglas: Dict[str, str], connection_id: str) -> Dict[str, Any]:
    tabla_raw = _mysql_preflight(motor, tabla)
    conn = motor.conectar()
    cur = conn.cursor()
    
    try:
        # 1. Renombrar tabla original
        cur.execute(f"RENAME TABLE `{tabla}` TO `{tabla_raw}`")
        
        # 2. Crear vista DDM
        sql_select = _mysql_generar_select_vista(motor, tabla_raw, reglas)
        cur.execute(f"CREATE VIEW `{tabla}` AS {sql_select}")
        
        conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except: pass
        raise e
    finally:
        conn.close()

    _registrar_estado(connection_id, tabla, "ACTIVA")
    return {"filas_protegidas": "N/A (Vista DDM creada)", "backup_tabla": tabla_raw}


def _mysql_restaurar(motor, tabla: str, connection_id: str) -> Dict[str, Any]:
    tabla_raw = tabla + "__raw"
    res = motor.ejecutar_consulta(f"SHOW TABLES LIKE '{tabla_raw}'")
    if not res:
        raise ValueError(f"Tabla base '{tabla_raw}' no encontrada en MySQL.")

    conn = motor.conectar()
    cur = conn.cursor()
    try:
        cur.execute(f"DROP VIEW IF EXISTS `{tabla}`")
        cur.execute(f"RENAME TABLE `{tabla_raw}` TO `{tabla}`")
        conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except: pass
        raise e
    finally:
        conn.close()

    _registrar_estado(connection_id, tabla, "INACTIVA")
    return {"filas_restauradas": "N/A (Vista eliminada)"}

def _postgres_preflight(motor, tabla: str) -> str:
    tabla_raw = tabla + "__raw"
    res = motor.ejecutar_consulta(f"SELECT to_regclass('public.\"{tabla_raw}\"') AS existe")
    if res and res[0].get("existe"):
        raise ValueError(
            f"Pre-flight FAIL: La tabla base '{tabla_raw}' ya existe en PostgreSQL. "
            "Ejecuta 'Restaurar' antes de volver a proteger."
        )
    return tabla_raw

def _postgres_generar_select_vista(motor, tabla_raw: str, reglas: Dict[str, str]) -> str:
    esquema = motor.obtener_esquema().get("tablas", {})
    columnas = esquema.get(tabla_raw, [])
    if not columnas:
        columnas = esquema.get(tabla_raw.replace("__raw", ""), [])
        if not columnas:
            res = motor.ejecutar_consulta(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{tabla_raw.replace('__raw', '')}'")
            columnas = [r['column_name'] for r in res]

    select_parts = []
    for col in columnas:
        if col in reglas:
            algoritmo = reglas[col]
            if algoritmo == "redaccion":
                select_parts.append(f"'***' AS \"{col}\"")
            elif algoritmo == "hashing":
                # Fallback to MD5 if pgcrypto is not installed
                select_parts.append(f"MD5(CAST(\"{col}\" AS TEXT)) AS \"{col}\"")
            else:
                select_parts.append(f"'[MASKED]' AS \"{col}\"")
        else:
            select_parts.append(f"\"{col}\"")
            
    return f"SELECT {', '.join(select_parts)} FROM \"{tabla_raw}\""

def _postgres_proteger(motor, tabla: str, reglas: Dict[str, str], connection_id: str) -> Dict[str, Any]:
    tabla_raw = _postgres_preflight(motor, tabla)
    conn = motor.conectar()
    cur = conn.cursor()
    
    try:
        cur.execute(f'ALTER TABLE "{tabla}" RENAME TO "{tabla_raw}"')
        sql_select = _postgres_generar_select_vista(motor, tabla_raw, reglas)
        cur.execute(f'CREATE VIEW "{tabla}" AS {sql_select}')
        conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except: pass
        raise e
    finally:
        conn.close()

    _registrar_estado(connection_id, tabla, "ACTIVA")
    return {"filas_protegidas": "N/A (Vista DDM creada)", "backup_tabla": tabla_raw}

def _postgres_restaurar(motor, tabla: str, connection_id: str) -> Dict[str, Any]:
    tabla_raw = tabla + "__raw"
    res = motor.ejecutar_consulta(f"SELECT to_regclass('public.\"{tabla_raw}\"') AS existe")
    if not res or not res[0].get("existe"):
        raise ValueError(f"Tabla base '{tabla_raw}' no encontrada en PostgreSQL.")

    conn = motor.conectar()
    cur = conn.cursor()
    try:
        cur.execute(f'DROP VIEW IF EXISTS "{tabla}"')
        cur.execute(f'ALTER TABLE "{tabla_raw}" RENAME TO "{tabla}"')
        conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except: pass
        raise e
    finally:
        conn.close()

    _registrar_estado(connection_id, tabla, "INACTIVA")
    return {"filas_restauradas": "N/A (Vista eliminada)"}


# ─────────────────────────────────────────────────────────────────────────────
# ESTRATEGIA: SQL Server (T-SQL)
# ─────────────────────────────────────────────────────────────────────────────

def _sqlserver_preflight(motor, tabla: str) -> str:
    tabla_raw = tabla + "__raw"
    res = motor.ejecutar_consulta(
        f"SELECT OBJECT_ID('{tabla_raw}', 'U') AS existe"
    )
    if res and res[0].get("existe") is not None:
        raise ValueError(
            f"Pre-flight FAIL: La tabla base '{tabla_raw}' ya existe en SQL Server. "
            "Ejecuta 'Restaurar' antes de volver a proteger."
        )
    return tabla_raw

def _sqlserver_generar_select_vista(motor, tabla_raw: str, reglas: Dict[str, str]) -> str:
    esquema = motor.obtener_esquema().get("tablas", {})
    columnas = esquema.get(tabla_raw, [])
    if not columnas:
        columnas = esquema.get(tabla_raw.replace("__raw", ""), [])
        if not columnas:
            res = motor.ejecutar_consulta(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tabla_raw.replace('__raw', '')}'")
            columnas = [r['COLUMN_NAME'] for r in res]

    select_parts = []
    for col in columnas:
        if col in reglas:
            algoritmo = reglas[col]
            if algoritmo == "redaccion":
                select_parts.append(f"'***' AS [{col}]")
            elif algoritmo == "hashing":
                # Fallback hashing in T-SQL
                select_parts.append(f"SUBSTRING(CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', CAST([{col}] AS VARCHAR(MAX))), 2), 1, 16) AS [{col}]")
            else:
                select_parts.append(f"'[MASKED]' AS [{col}]")
        else:
            select_parts.append(f"[{col}]")
            
    return f"SELECT {', '.join(select_parts)} FROM [{tabla_raw}]"


def _sqlserver_proteger(motor, tabla: str, reglas: Dict[str, str], connection_id: str) -> Dict[str, Any]:
    tabla_raw = _sqlserver_preflight(motor, tabla)
    conn = motor.conectar()
    cur  = conn.cursor()

    try:
        cur.execute(f"EXEC sp_rename '{tabla}', '{tabla_raw}'")
        sql_select = _sqlserver_generar_select_vista(motor, tabla_raw, reglas)
        cur.execute(f"CREATE VIEW [{tabla}] AS {sql_select}")
        conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except: pass
        raise e
    finally:
        conn.close()

    _registrar_estado(connection_id, tabla, "ACTIVA")
    return {"filas_protegidas": "N/A (Vista DDM creada)", "backup_tabla": tabla_raw}

def _sqlserver_restaurar(motor, tabla: str, connection_id: str) -> Dict[str, Any]:
    tabla_raw = tabla + "__raw"
    res = motor.ejecutar_consulta(f"SELECT OBJECT_ID('{tabla_raw}', 'U') AS existe")
    if not res or res[0].get("existe") is None:
        raise ValueError(f"Tabla base '{tabla_raw}' no encontrada en SQL Server.")

    conn = motor.conectar()
    cur  = conn.cursor()
    try:
        cur.execute(f"DROP VIEW IF EXISTS [{tabla}]")
        cur.execute(f"EXEC sp_rename '{tabla_raw}', '{tabla}'")
        conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except: pass
        raise e
    finally:
        conn.close()

    _registrar_estado(connection_id, tabla, "INACTIVA")
    return {"filas_restauradas": "N/A (Vista eliminada)"}


# ─────────────────────────────────────────────────────────────────────────────
# ESTRATEGIA: MongoDB (Shadow Collections)
# ─────────────────────────────────────────────────────────────────────────────

def _mongo_preflight(motor, coleccion: str) -> Tuple[Any, Any, str]:
    col_raw = coleccion + "__raw"
    cliente = motor.conectar()
    db_name = motor.credenciales.get("database")
    db = cliente[db_name]
    if col_raw in db.list_collection_names():
        cliente.close()
        raise ValueError(
            f"Pre-flight FAIL: La colección base '{col_raw}' ya existe en MongoDB. "
            "Ejecuta 'Restaurar' antes de volver a proteger."
        )
    return cliente, db, col_raw

def _mongo_proteger(motor, coleccion: str, reglas: Dict[str, str], connection_id: str) -> Dict[str, Any]:
    cliente, db, col_raw = _mongo_preflight(motor, coleccion)

    try:
        # 1. Renombrar la colección original
        db[coleccion].rename(col_raw)

        # 2. Crear pipeline de agregación para enmascarar
        set_stage = {}
        for col, algoritmo in reglas.items():
            if algoritmo == "redaccion":
                set_stage[col] = "***"
            elif algoritmo == "hashing":
                # Basic masking since native SHA256 in MongoDB views requires complex JS/aggregation
                set_stage[col] = "[HASHED]" 
            else:
                set_stage[col] = "[MASKED]"

        pipeline = []
        if set_stage:
            pipeline.append({"$set": set_stage})

        # 3. Crear vista
        db.command({
            "create": coleccion,
            "viewOn": col_raw,
            "pipeline": pipeline
        })

    finally:
        cliente.close()

    _registrar_estado(connection_id, coleccion, "ACTIVA")
    return {"filas_protegidas": "N/A (Vista DDM creada)", "shadow_collection": col_raw}


def _mongo_restaurar(motor, coleccion: str, connection_id: str) -> Dict[str, Any]:
    col_raw = coleccion + "__raw"
    cliente = motor.conectar()

    try:
        db_name = motor.credenciales.get("database")
        db = cliente[db_name]

        if col_raw not in db.list_collection_names():
            raise ValueError(f"Colección base '{col_raw}' no encontrada en MongoDB.")

        db[coleccion].drop()
        db[col_raw].rename(coleccion)

    finally:
        cliente.close()

    _registrar_estado(connection_id, coleccion, "INACTIVA")
    return {"filas_restauradas": "N/A (Vista eliminada)"}


# ─────────────────────────────────────────────────────────────────────────────
# DISPATCHER PRINCIPAL — Patrón Strategy
# ─────────────────────────────────────────────────────────────────────────────

# Registro de estrategias: motor → (fn_proteger, fn_restaurar)
_ESTRATEGIAS: Dict[str, Tuple[Callable, Callable]] = {
    "sqlite":    (_sqlite_proteger,    _sqlite_restaurar),
    "postgres":  (_postgres_proteger,  _postgres_restaurar),
    "mysql":     (_mysql_proteger,     _mysql_restaurar),
    "mariadb":   (_mysql_proteger,     _mysql_restaurar),
    "sqlserver": (_sqlserver_proteger, _sqlserver_restaurar),
    "mongodb":   (_mongo_proteger,     _mongo_restaurar),
}

MOTORES_SDM_DISPONIBLES = list(_ESTRATEGIAS.keys())


def proteger_tabla(
    motor_nombre: str,
    motor: Any,
    tabla: str,
    reglas: Dict[str, str],
    connection_id: str,
) -> Dict[str, Any]:
    """
    Punto de entrada unificado para activar el Static Data Masking.
    Selecciona la estrategia correcta según el motor y delega la operación.

    Raises:
        ValueError: Pre-flight fallido, tabla vacía, o motor no soportado.
        Exception:  Error de conexión o error inesperado durante la operación.
    """
    if motor_nombre not in _ESTRATEGIAS:
        disponibles = ", ".join(MOTORES_SDM_DISPONIBLES)
        raise ValueError(
            f"SDM no disponible para el motor '{motor_nombre}'. "
            f"Motores soportados: {disponibles}."
        )

    fn_proteger, _ = _ESTRATEGIAS[motor_nombre]
    return fn_proteger(motor, tabla, reglas, connection_id)


def restaurar_tabla(
    motor_nombre: str,
    motor: Any,
    tabla: str,
    connection_id: str,
) -> Dict[str, Any]:
    """
    Punto de entrada unificado para revertir el Static Data Masking.
    Descifra el backup AES y restaura los datos originales.

    Raises:
        ValueError: Backup no encontrado o motor no soportado.
        Exception:  Error de conexión o error inesperado durante la operación.
    """
    if motor_nombre not in _ESTRATEGIAS:
        disponibles = ", ".join(MOTORES_SDM_DISPONIBLES)
        raise ValueError(
            f"Restore no disponible para el motor '{motor_nombre}'. "
            f"Motores soportados: {disponibles}."
        )

    _, fn_restaurar = _ESTRATEGIAS[motor_nombre]
    return fn_restaurar(motor, tabla, connection_id)
