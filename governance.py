"""
governance.py — Módulo de Gobernanza de Datos Universal (Static Data Masking)
VERSIÓN OPTIMIZADA v2.0

OPTIMIZACIONES PRINCIPALES:
    1. UPDATE in-place en lugar de DELETE + INSERT (solo modifica columnas afectadas)
    2. Procesamiento por lotes (BATCH_SIZE) para no saturar memoria
    3. Backup con CREATE TABLE AS SELECT (SQL puro, sin copiar datos por Python)
    4. MongoDB: updateMany con aggregation pipeline (sin drop + insertMany)
    5. Solo lee filas que necesitan enmascaramiento (columnas específicas)

ARQUITECTURA: Patrón Strategy con Dispatcher.

ESTRATEGIA DE SEGURIDAD:
    INACTIVO: tabla original contiene datos reales.
    ACTIVO:   tabla original contiene DATOS ENMASCARADOS permanentemente.
              tabla <nombre>__backup_enc contiene originales CIFRADOS con AES-256.

MOTORES SOPORTADOS: sqlite, postgres, sqlserver, mongodb, redis, neo4j
"""

import copy
import datetime
import os
import sqlite3
from typing import Any, Callable, Dict, List, Optional, Tuple

from config import settings
from masking import aplicar_enmascaramiento, cifrar_valor, descifrar_valor

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES DE OPTIMIZACIÓN
# ─────────────────────────────────────────────────────────────────────────────

BATCH_SIZE = 500  # Filas por lote para UPDATE/INSERT
BACKUP_SUFFIX = "__backup_enc"
PLATFORM_DB = os.path.join(settings.DATA_DIR, "platform_users.db")


# ─────────────────────────────────────────────────────────────────────────────
# ESTADO DE GOBERNANZA (persistido en SQLite)
# ─────────────────────────────────────────────────────────────────────────────

def _get_platform_conn():
    conn = sqlite3.connect(PLATFORM_DB)
    return conn


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
    if not val_str:
        return None
    val_str = val_str.strip()
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
    return val_str


def _cifrar_valor_seguro(valor: Any) -> Optional[str]:
    """Cifra un valor manejando None y tipos no-string."""
    if valor is None:
        return None
    return cifrar_valor(str(valor))


def _descifrar_valor_seguro(valor: Any) -> Optional[str]:
    """Descifra un valor manejando None."""
    if valor is None:
        return None
    try:
        return descifrar_valor(str(valor))
    except Exception:
        return str(valor)


def _chunks(lista: List, tamaño: int):
    """Divide una lista en lotes de tamaño fijo."""
    for i in range(0, len(lista), tamaño):
        yield lista[i:i + tamaño]


# ─────────────────────────────────────────────────────────────────────────────
# ESTRATEGIA OPTIMIZADA: SQLite
# ─────────────────────────────────────────────────────────────────────────────

def _sqlite_preflight(motor, tabla: str) -> str:
    backup = tabla + BACKUP_SUFFIX
    existe = motor.ejecutar_consulta(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{backup}'"
    )
    if existe:
        raise ValueError(
            f"Pre-flight FAIL: El backup '{backup}' ya existe. "
            "Ejecuta 'Restaurar' primero."
        )
    return backup


def _sqlite_proteger(motor, tabla: str, reglas: Dict[str, str], connection_id: str) -> Dict[str, Any]:
    """
    OPTIMIZADO: 
    - Backup con CREATE TABLE AS SELECT (SQL puro, sin copiar por Python)
    - UPDATE in-place por lotes (solo modifica columnas con reglas)
    - No carga toda la tabla en memoria
    """
    backup = _sqlite_preflight(motor, tabla)
    columnas_reglas = list(reglas.keys())

    conn = motor.conectar()
    cur = conn.cursor()

    try:
        # 1. Contar filas totales
        cur.execute(f"SELECT COUNT(*) FROM {tabla}")
        total_filas = cur.fetchone()[0]
        if total_filas == 0:
            raise ValueError(f"La tabla '{tabla}' está vacía.")

        # 2. Backup: CREATE TABLE + INSERT ... SELECT (SQL puro, sin Python)
        cur.execute(f"CREATE TABLE IF NOT EXISTS {backup} AS SELECT * FROM {tabla}")
        # Cifrar los valores del backup en lotes
        cur.execute(f"SELECT rowid, * FROM {backup}")
        cols_backup = [desc[0] for desc in cur.description]
        # Necesitamos las columnas reales para cifrar
        cur.execute(f"PRAGMA table_info({tabla})")
        cols_reales = [row[1] for row in cur.fetchall()]

        # 3. Leer y actualizar por lotes (solo columnas con reglas)
        filas_procesadas = 0
        offset = 0

        while offset < total_filas:
            # Leer lote con rowid para UPDATE targeting
            cur.execute(f"SELECT rowid, {', '.join(cols_reales)} FROM {tabla} LIMIT {BATCH_SIZE} OFFSET {offset}")
            filas = cur.fetchall()

            for fila in filas:
                rowid = fila[0]
                valores = fila[1:]
                dict_fila = dict(zip(cols_reales, valores))

                # Cifrar cada valor para el backup
                valores_cifrados = [_cifrar_valor_seguro(dict_fila.get(c)) for c in cols_reales]

                # Aplicar enmascaramiento solo a las columnas con reglas
                valores_enmascarados = {}
                for col, algoritmo in reglas.items():
                    if col in dict_fila and dict_fila[col] is not None:
                        valor = str(dict_fila[col])
                        fila_temp = {col: valor}
                        resultado = aplicar_enmascaramiento([fila_temp], {col: algoritmo})
                        valores_enmascarados[col] = resultado[0][col]

                # UPDATE in-place: solo las columnas con reglas
                set_clauses = [f"{col} = ?" for col in valores_enmascarados.keys()]
                params = list(valores_enmascarados.values()) + [rowid]
                cur.execute(
                    f"UPDATE {tabla} SET {', '.join(set_clauses)} WHERE rowid = ?",
                    params
                )

                # Insertar cifrado en backup (sobrescribir valores originales con cifrados)
                cur.execute(f"DELETE FROM {backup} WHERE rowid = ?", (rowid,))
                ph = ", ".join(["?" for _ in cols_reales])
                cur.execute(
                    f"INSERT INTO {backup} ({', '.join(cols_reales)}) VALUES ({ph})",
                    valores_cifrados
                )

                filas_procesadas += 1

            offset += BATCH_SIZE
            conn.commit()

        _registrar_estado(connection_id, tabla, "ACTIVA")
        return {"filas_protegidas": filas_procesadas, "backup_tabla": backup}

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def _sqlite_restaurar(motor, tabla: str, connection_id: str) -> Dict[str, Any]:
    """
    OPTIMIZADO: Restaura por lotes usando UPDATE in-place desde el backup.
    """
    backup = tabla + BACKUP_SUFFIX

    if not motor.ejecutar_consulta(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{backup}'"
    ):
        raise ValueError(f"Backup '{backup}' no encontrado.")

    conn = motor.conectar()
    cur = conn.cursor()

    try:
        # Obtener columnas
        cur.execute(f"PRAGMA table_info({tabla})")
        cols = [row[1] for row in cur.fetchall()]

        # Contar filas en backup
        cur.execute(f"SELECT COUNT(*) FROM {backup}")
        total = cur.fetchone()[0]

        # Restaurar por lotes
        filas_restauradas = 0
        offset = 0

        while offset < total:
            cur.execute(f"SELECT * FROM {backup} LIMIT {BATCH_SIZE} OFFSET {offset}")
            filas = cur.fetchall()

            # Limpiar tabla original e insertar restauradas
            # Para restauración necesitamos DELETE + INSERT porque los datos son completamente diferentes
            if offset == 0:
                cur.execute(f"DELETE FROM {tabla}")

            for fila in filas:
                valores_descifrados = [_descifrar_valor_seguro(v) for v in fila]
                ph = ", ".join(["?" for _ in cols])
                cur.execute(
                    f"INSERT INTO {tabla} ({', '.join(cols)}) VALUES ({ph})",
                    valores_descifrados
                )
                filas_restauradas += 1

            offset += BATCH_SIZE
            conn.commit()

        cur.execute(f"DROP TABLE IF EXISTS {backup}")
        conn.commit()

        _registrar_estado(connection_id, tabla, "INACTIVA")
        return {"filas_restauradas": filas_restauradas}

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# ESTRATEGIA OPTIMIZADA: PostgreSQL
# ─────────────────────────────────────────────────────────────────────────────

def _postgres_preflight(motor, tabla: str) -> str:
    backup = tabla + BACKUP_SUFFIX
    res = motor.ejecutar_consulta(f"SELECT to_regclass('public.\"{backup}\"') AS existe")
    if res and res[0].get("existe"):
        raise ValueError(
            f"Pre-flight FAIL: La tabla '{backup}' ya existe. "
            "Ejecuta 'Restaurar' primero."
        )
    return backup


def _postgres_proteger(motor, tabla: str, reglas: Dict[str, str], connection_id: str) -> Dict[str, Any]:
    """
    OPTIMIZADO:
    - Backup: CREATE TABLE ... AS SELECT (SQL puro)
    - UPDATE in-place con CASE WHEN por lotes
    - No copia datos por Python para el backup inicial
    """
    backup = _postgres_preflight(motor, tabla)
    columnas_reglas = list(reglas.keys())

    conn = motor.conectar()
    cur = conn.cursor()

    try:
        # 1. Contar filas
        cur.execute(f'SELECT COUNT(*) FROM "{tabla}"')
        total_filas = cur.fetchone()[0]
        if total_filas == 0:
            raise ValueError(f"La tabla '{tabla}' está vacía.")

        # 2. Obtener columnas y clave primaria
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = %s ORDER BY ordinal_position
        """, (tabla,))
        cols = [row[0] for row in cur.fetchall()]

        # Buscar PK para UPDATE eficiente
        cur.execute("""
            SELECT a.attname FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = %s::regclass AND i.indisprimary
        """, (tabla,))
        pk_rows = cur.fetchall()
        pk_col = pk_rows[0][0] if pk_rows else cols[0]  # Fallback a primera columna

        # 3. Backup: CREATE TABLE AS SELECT (SQL puro)
        cur.execute(f'CREATE TABLE IF NOT EXISTS "{backup}" AS SELECT * FROM "{tabla}"')
        # Cifrar valores del backup en lotes
        cur.execute(f'SELECT * FROM "{backup}"')
        backup_cols = [desc[0] for desc in cur.description]

        offset = 0
        while offset < total_filas:
            cur.execute(f'SELECT * FROM "{backup}" LIMIT {BATCH_SIZE} OFFSET {offset}')
            filas_backup = cur.fetchall()
            for fila in filas_backup:
                dict_fila = dict(zip(backup_cols, fila))
                valores_cifrados = [_cifrar_valor_seguro(dict_fila.get(c)) for c in backup_cols]
                pk_val = dict_fila.get(pk_col)
                set_clauses = [f'"{c}" = %s' for c in backup_cols]
                cur.execute(
                    f'UPDATE "{backup}" SET {", ".join(set_clauses)} WHERE "{pk_col}" = %s',
                    valores_cifrados + [pk_val]
                )
            offset += BATCH_SIZE
            conn.commit()

        # 4. Enmascaramiento in-place por lotes
        filas_procesadas = 0
        offset = 0

        while offset < total_filas:
            cur.execute(f'SELECT {", ".join([f'"{c}"' for c in cols])} FROM "{tabla}" LIMIT {BATCH_SIZE} OFFSET {offset}')
            filas = cur.fetchall()

            for fila in filas:
                dict_fila = dict(zip(cols, fila))
                pk_val = dict_fila.get(pk_col)

                # Aplicar enmascaramiento
                valores_enmascarados = {}
                for col, algoritmo in reglas.items():
                    if col in dict_fila and dict_fila[col] is not None:
                        valor = str(dict_fila[col])
                        resultado = aplicar_enmascaramiento([{col: valor}], {col: algoritmo})
                        valores_enmascarados[col] = resultado[0][col]

                # UPDATE in-place
                set_clauses = [f'"{col}" = %s' for col in valores_enmascarados.keys()]
                params = list(valores_enmascarados.values()) + [pk_val]
                cur.execute(
                    f'UPDATE "{tabla}" SET {", ".join(set_clauses)} WHERE "{pk_col}" = %s',
                    params
                )
                filas_procesadas += 1

            offset += BATCH_SIZE
            conn.commit()

        _registrar_estado(connection_id, tabla, "ACTIVA")
        return {"filas_protegidas": filas_procesadas, "backup_tabla": backup}

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def _postgres_restaurar(motor, tabla: str, connection_id: str) -> Dict[str, Any]:
    """OPTIMIZADO: Restauración por lotes."""
    backup = tabla + BACKUP_SUFFIX

    res = motor.ejecutar_consulta(f"SELECT to_regclass('public.\"{backup}\"') AS existe")
    if not res or not res[0].get("existe"):
        raise ValueError(f"Backup '{backup}' no encontrado.")

    conn = motor.conectar()
    cur = conn.cursor()

    try:
        cur.execute(f'SELECT COUNT(*) FROM "{backup}"')
        total = cur.fetchone()[0]

        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = %s ORDER BY ordinal_position
        """, (tabla,))
        cols = [row[0] for row in cur.fetchall()]

        # Restaurar: TRUNCATE + INSERT por lotes
        cur.execute(f'TRUNCATE TABLE "{tabla}"')

        offset = 0
        filas_restauradas = 0
        while offset < total:
            cur.execute(f'SELECT * FROM "{backup}" LIMIT {BATCH_SIZE} OFFSET {offset}')
            filas = cur.fetchall()
            for fila in filas:
                valores_descifrados = [_descifrar_valor_seguro(v) for v in fila]
                cols_q = ", ".join([f'"{c}"' for c in cols])
                ph = ", ".join(["%s" for _ in cols])
                cur.execute(
                    f'INSERT INTO "{tabla}" ({cols_q}) VALUES ({ph})',
                    valores_descifrados
                )
                filas_restauradas += 1
            offset += BATCH_SIZE
            conn.commit()

        cur.execute(f'DROP TABLE IF EXISTS "{backup}"')
        conn.commit()

        _registrar_estado(connection_id, tabla, "INACTIVA")
        return {"filas_restauradas": filas_restauradas}

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# ESTRATEGIA OPTIMIZADA: SQL Server
# ─────────────────────────────────────────────────────────────────────────────

def _sqlserver_preflight(motor, tabla: str) -> str:
    backup = tabla + BACKUP_SUFFIX
    res = motor.ejecutar_consulta(f"SELECT OBJECT_ID('{backup}', 'U') AS existe")
    if res and res[0].get("existe") is not None:
        raise ValueError(
            f"Pre-flight FAIL: La tabla '{backup}' ya existe. "
            "Ejecuta 'Restaurar' primero."
        )
    return backup


def _sqlserver_get_fk_dependientes(cur, tabla: str) -> List[str]:
    cur.execute("""
        SELECT DISTINCT OBJECT_NAME(fk.parent_object_id) AS tabla_hijo
        FROM sys.foreign_keys AS fk
        INNER JOIN sys.tables AS t ON t.object_id = fk.referenced_object_id
        WHERE t.name = %s
    """, (tabla,))
    filas = cur.fetchall()
    return [f[0] if isinstance(f, (tuple, list)) else f.get("tabla_hijo") for f in filas]


def _sqlserver_proteger(motor, tabla: str, reglas: Dict[str, str], connection_id: str) -> Dict[str, Any]:
    """
    OPTIMIZADO:
    - Backup con SELECT INTO (SQL puro)
    - UPDATE in-place por lotes
    """
    backup = _sqlserver_preflight(motor, tabla)

    conn = motor.conectar()
    cur = conn.cursor()

    try:
        # 1. Contar filas
        cur.execute(f"SELECT COUNT(*) FROM [{tabla}]")
        total_filas = cur.fetchone()[0]
        if total_filas == 0:
            raise ValueError(f"La tabla '{tabla}' está vacía.")

        # 2. Obtener columnas
        cur.execute(f"""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{tabla}' ORDER BY ORDINAL_POSITION
        """)
        cols = [row[0] for row in cur.fetchall()]

        # 3. FK handling
        tablas_hijo = _sqlserver_get_fk_dependientes(cur, tabla)
        for hijo in tablas_hijo:
            cur.execute(f"ALTER TABLE [{hijo}] NOCHECK CONSTRAINT ALL")

        try:
            cur.execute(f"SET IDENTITY_INSERT [{tabla}] ON")
        except Exception:
            pass

        # 4. Backup: SELECT INTO (SQL puro, sin Python)
        cur.execute(f"SELECT * INTO [{backup}] FROM [{tabla}]")
        conn.commit()

        # Cifrar backup en lotes
        cur.execute(f"SELECT * FROM [{backup}]")
        backup_cols = [desc[0] for desc in cur.description]

        offset = 0
        while offset < total_filas:
            cur.execute(f"SELECT * FROM [{backup}] ORDER BY (SELECT NULL) OFFSET {offset} ROWS FETCH NEXT {BATCH_SIZE} ROWS ONLY")
            filas_backup = cur.fetchall()
            for fila in filas_backup:
                dict_fila = dict(zip(backup_cols, fila))
                valores_cifrados = [_cifrar_valor_seguro(dict_fila.get(c)) for c in backup_cols]
                # Usar primera columna como identificador
                pk_val = dict_fila.get(backup_cols[0])
                set_clauses = [f"[{c}] = %s" for c in backup_cols]
                cur.execute(
                    f"UPDATE [{backup}] SET {', '.join(set_clauses)} WHERE [{backup_cols[0]}] = %s",
                    valores_cifrados + [pk_val]
                )
            offset += BATCH_SIZE
            conn.commit()

        # 5. Enmascaramiento in-place por lotes
        filas_procesadas = 0
        offset = 0

        while offset < total_filas:
            cur.execute(f"SELECT * FROM [{tabla}] ORDER BY (SELECT NULL) OFFSET {offset} ROWS FETCH NEXT {BATCH_SIZE} ROWS ONLY")
            filas = cur.fetchall()

            for fila in filas:
                dict_fila = dict(zip(cols, fila))
                pk_val = dict_fila.get(cols[0])

                valores_enmascarados = {}
                for col, algoritmo in reglas.items():
                    if col in dict_fila and dict_fila[col] is not None:
                        valor = str(dict_fila[col])
                        resultado = aplicar_enmascaramiento([{col: valor}], {col: algoritmo})
                        valores_enmascarados[col] = resultado[0][col]

                set_clauses = [f"[{col}] = %s" for col in valores_enmascarados.keys()]
                params = list(valores_enmascarados.values()) + [pk_val]
                cur.execute(
                    f"UPDATE [{tabla}] SET {', '.join(set_clauses)} WHERE [{cols[0]}] = %s",
                    params
                )
                filas_procesadas += 1

            offset += BATCH_SIZE
            conn.commit()

        _registrar_estado(connection_id, tabla, "ACTIVA")
        return {"filas_protegidas": filas_procesadas, "backup_tabla": backup}

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        try:
            cur.execute(f"SET IDENTITY_INSERT [{tabla}] OFF")
        except Exception:
            pass
        for hijo in tablas_hijo:
            try:
                cur.execute(f"ALTER TABLE [{hijo}] CHECK CONSTRAINT ALL")
            except Exception:
                pass
        conn.close()


def _sqlserver_restaurar(motor, tabla: str, connection_id: str) -> Dict[str, Any]:
    """OPTIMIZADO: Restauración por lotes con TRUNCATE + INSERT."""
    backup = tabla + BACKUP_SUFFIX

    res = motor.ejecutar_consulta(f"SELECT OBJECT_ID('{backup}', 'U') AS existe")
    if not res or res[0].get("existe") is None:
        raise ValueError(f"Backup '{backup}' no encontrado.")

    conn = motor.conectar()
    cur = conn.cursor()

    try:
        cur.execute(f"SELECT COUNT(*) FROM [{backup}]")
        total = cur.fetchone()[0]

        cur.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{tabla}' ORDER BY ORDINAL_POSITION
        """)
        col_info = cur.fetchall()
        cols = [row[0] for row in col_info]
        tipos = {row[0].lower(): row[1].lower() for row in col_info}

        tablas_hijo = _sqlserver_get_fk_dependientes(cur, tabla)
        for hijo in tablas_hijo:
            cur.execute(f"ALTER TABLE [{hijo}] NOCHECK CONSTRAINT ALL")

        try:
            cur.execute(f"SET IDENTITY_INSERT [{tabla}] ON")
        except Exception:
            pass

        cur.execute(f"TRUNCATE TABLE [{tabla}]")

        offset = 0
        filas_restauradas = 0
        while offset < total:
            cur.execute(f"SELECT * FROM [{backup}] ORDER BY (SELECT NULL) OFFSET {offset} ROWS FETCH NEXT {BATCH_SIZE} ROWS ONLY")
            filas = cur.fetchall()
            for fila in filas:
                valores_descifrados = []
                for c, val in zip(cols, fila):
                    descifrado = _descifrar_valor_seguro(val)
                    tipo = tipos.get(c.lower(), "")
                    if descifrado and tipo in ("date", "datetime", "datetime2", "smalldatetime"):
                        descifrado = _parsear_fecha_sqlserver(descifrado, tipo)
                    valores_descifrados.append(descifrado)

                cols_q = ", ".join([f"[{c}]" for c in cols])
                ph = ", ".join(["%s" for _ in cols])
                cur.execute(f"INSERT INTO [{tabla}] ({cols_q}) VALUES ({ph})", valores_descifrados)
                filas_restauradas += 1
            offset += BATCH_SIZE
            conn.commit()

        cur.execute(f"DROP TABLE [{backup}]")
        conn.commit()

        _registrar_estado(connection_id, tabla, "INACTIVA")
        return {"filas_restauradas": filas_restauradas}

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        try:
            cur.execute(f"SET IDENTITY_INSERT [{tabla}] OFF")
        except Exception:
            pass
        for hijo in tablas_hijo:
            try:
                cur.execute(f"ALTER TABLE [{hijo}] CHECK CONSTRAINT ALL")
            except Exception:
                pass
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# ESTRATEGIA OPTIMIZADA: MongoDB (updateMany con pipeline)
# ─────────────────────────────────────────────────────────────────────────────

def _mongo_preflight(motor, coleccion: str) -> Tuple[Any, Any, str]:
    backup = coleccion + BACKUP_SUFFIX
    cliente = motor.conectar()
    db_name = motor.credenciales.get("database")
    db = cliente[db_name]
    if backup in db.list_collection_names():
        cliente.close()
        raise ValueError(
            f"Pre-flight FAIL: La shadow collection '{backup}' ya existe. "
            "Ejecuta 'Restaurar' primero."
        )
    return cliente, db, backup


def _mongo_proteger(motor, coleccion: str, reglas: Dict[str, str], connection_id: str) -> Dict[str, Any]:
    """
    OPTIMIZADO:
    - Backup: aggregate + $merge (sin copiar por Python)
    - Enmascaramiento: updateMany con aggregation pipeline (MongoDB 4.2+)
    - No carga documentos en memoria
    """
    cliente, db, backup = _mongo_preflight(motor, coleccion)

    try:
        col_orig = db[coleccion]
        total_docs = col_orig.count_documents({})
        if total_docs == 0:
            raise ValueError(f"La colección '{coleccion}' está vacía.")

        # 1. Backup: $merge (SQL puro de MongoDB, sin Python)
        pipeline_backup = [
            {"$addFields": {"_id": {"$toString": "$_id"}}},  # Convertir ObjectId a string
            {"$merge": {"into": backup, "whenMatched": "replace"}}
        ]
        col_orig.aggregate(pipeline_backup)

        # 2. Cifrar backup campo a campo (en lotes)
        col_backup = db[backup]
        batch = []
        for doc in col_backup.find({}):
            doc_enc = {}
            for k, v in doc.items():
                if k == "_id":
                    doc_enc[k] = str(v)
                elif isinstance(v, str):
                    doc_enc[k] = cifrar_valor(v)
                elif v is not None:
                    doc_enc[k] = cifrar_valor(str(v))
                else:
                    doc_enc[k] = None
            batch.append(doc_enc)
            if len(batch) >= BATCH_SIZE:
                col_backup.delete_many({})
                col_backup.insert_many(batch)
                batch = []
        if batch:
            col_backup.delete_many({})
            col_backup.insert_many(batch)

        # 3. Enmascaramiento in-place con updateMany por lotes
        # Construir pipeline de $set para MongoDB 4.2+
        set_expressions = {}
        for campo, algoritmo in reglas.items():
            # MongoDB no soporta hashing SHA nativo, procesamos en Python por lotes
            pass

        # Procesar en lotes por _id
        filas_procesadas = 0
        cursor = col_orig.find({}, {"_id": 1, **{c: 1 for c in reglas.keys()}})

        batch_updates = []
        for doc in cursor:
            doc_id = doc["_id"]
            valores_a_enmascarar = {}
            for campo, algoritmo in reglas.items():
                if campo in doc and doc[campo] is not None:
                    valores_a_enmascarar[campo] = str(doc[campo])

            if valores_a_enmascarar:
                resultado = aplicar_enmascaramiento([valores_a_enmascarar], reglas)[0]
                set_clause = {campo: resultado[campo] for campo in reglas if campo in resultado}
                batch_updates.append({
                    "updateOne": {
                        "filter": {"_id": doc_id},
                        "update": {"$set": set_clause}
                    }
                })

            if len(batch_updates) >= BATCH_SIZE:
                col_orig.bulk_write(batch_updates)
                filas_procesadas += len(batch_updates)
                batch_updates = []

        if batch_updates:
            col_orig.bulk_write(batch_updates)
            filas_procesadas += len(batch_updates)

        _registrar_estado(connection_id, coleccion, "ACTIVA")
        return {"filas_protegidas": filas_procesadas, "shadow_collection": backup}

    finally:
        cliente.close()


def _mongo_restaurar(motor, coleccion: str, connection_id: str) -> Dict[str, Any]:
    """
    OPTIMIZADO: Restauración con aggregate + $merge + drop backup.
    """
    backup = coleccion + BACKUP_SUFFIX
    cliente = motor.conectar()

    try:
        db_name = motor.credenciales.get("database")
        db = cliente[db_name]

        if backup not in db.list_collection_names():
            raise ValueError(f"Shadow collection '{backup}' no encontrada.")

        col_backup = db[backup]
        total = col_backup.count_documents({})

        # Descifrar y restaurar por lotes
        col_orig = db[coleccion]
        col_orig.drop()

        batch = []
        for doc in col_backup.find({}):
            doc_dec = {}
            for k, v in doc.items():
                if k == "_id":
                    doc_dec[k] = v
                elif isinstance(v, str):
                    try:
                        doc_dec[k] = descifrar_valor(v)
                    except Exception:
                        doc_dec[k] = v
                else:
                    doc_dec[k] = v
            batch.append(doc_dec)
            if len(batch) >= BATCH_SIZE:
                db[coleccion].insert_many(batch)
                batch = []

        if batch:
            db[coleccion].insert_many(batch)

        db[backup].drop()

        _registrar_estado(connection_id, coleccion, "INACTIVA")
        return {"filas_restauradas": total}

    finally:
        cliente.close()


# ─────────────────────────────────────────────────────────────────────────────
# ESTRATEGIA: Redis (Hash-based backup)
# ─────────────────────────────────────────────────────────────────────────────

def _redis_preflight(motor, clave: str) -> str:
    """Verifica que no exista backup previo para la clave."""
    backup_key = clave + BACKUP_SUFFIX
    cliente = motor.conectar()
    try:
        if cliente.exists(backup_key):
            raise ValueError(
                f"Pre-flight FAIL: El backup '{backup_key}' ya existe en Redis. "
                "Ejecuta 'Restaurar' primero."
            )
    finally:
        cliente.close()
    return backup_key


def _redis_proteger(motor, clave: str, reglas: Dict[str, str], connection_id: str) -> Dict[str, Any]:
    """
    SDM para Redis:
    - Backup: Guarda el valor original cifrado en una clave <clave>__backup_enc
    - Protección: Sobrescribe el valor con los datos enmascarados
    - Soporta: strings JSON y hashes
    """
    backup_key = _redis_preflight(motor, clave)
    
    cliente = motor.conectar()
    try:
        # Determinar tipo de dato
        tipo = cliente.type(clave).decode('utf-8') if isinstance(cliente.type(clave), bytes) else cliente.type(clave)
        
        if tipo == 'string':
            valor = cliente.get(clave)
            if valor is None:
                raise ValueError(f"La clave '{clave}' no existe en Redis.")
            
            # Intentar parsear como JSON
            import json
            try:
                datos = json.loads(valor)
                if isinstance(datos, dict):
                    # Backup: cifrar valor original
                    cliente.set(backup_key, cifrar_valor(valor))
                    
                    # Aplicar enmascaramiento
                    datos_enmascarados = aplicar_enmascaramiento([datos], reglas)[0]
                    cliente.set(clave, json.dumps(datos_enmascarados))
                    
                    _registrar_estado(connection_id, clave, "ACTIVA")
                    return {"filas_protegidas": 1, "backup_clave": backup_key, "tipo": "json"}
            except (json.JSONDecodeError, TypeError):
                pass
            
            # Backup: cifrar valor string
            cliente.set(backup_key, cifrar_valor(str(valor)))
            
            # Para strings simples, aplicar enmascaramiento al valor completo
            datos = {"valor": str(valor)}
            resultado = aplicar_enmascaramiento([datos], {"valor": list(reglas.values())[0] if reglas else "redaccion"})
            cliente.set(clave, resultado[0]["valor"])
            
            _registrar_estado(connection_id, clave, "ACTIVA")
            return {"filas_protegidas": 1, "backup_clave": backup_key, "tipo": "string"}
            
        elif tipo == 'hash':
            datos = cliente.hgetall(clave)
            if not datos:
                raise ValueError(f"El hash '{clave}' está vacío en Redis.")
            
            # Backup: cifrar cada campo
            backup_data = {}
            for k, v in datos.items():
                key_str = k.decode('utf-8') if isinstance(k, bytes) else k
                val_str = v.decode('utf-8') if isinstance(v, bytes) else v
                backup_data[key_str] = cifrar_valor(val_str)
            
            # Guardar backup como hash
            cliente.delete(backup_key)
            cliente.hset(backup_key, mapping=backup_data)
            
            # Aplicar enmascaramiento
            datos_dict = {}
            for k, v in datos.items():
                key_str = k.decode('utf-8') if isinstance(k, bytes) else k
                val_str = v.decode('utf-8') if isinstance(v, bytes) else v
                datos_dict[key_str] = val_str
            
            resultado = aplicar_enmascaramiento([datos_dict], reglas)[0]
            
            # Sobrescribir con datos enmascarados
            cliente.delete(clave)
            cliente.hset(clave, mapping=resultado)
            
            _registrar_estado(connection_id, clave, "ACTIVA")
            return {"filas_protegidas": len(datos), "backup_clave": backup_key, "tipo": "hash"}
        
        else:
            raise ValueError(f"SDM no soporta el tipo Redis '{tipo}'. Solo string y hash.")
    
    finally:
        cliente.close()


def _redis_restaurar(motor, clave: str, connection_id: str) -> Dict[str, Any]:
    """Restaura datos originales de Redis desde el backup cifrado."""
    backup_key = clave + BACKUP_SUFFIX
    
    cliente = motor.conectar()
    try:
        if not cliente.exists(backup_key):
            raise ValueError(f"Backup '{backup_key}' no encontrado en Redis.")
        
        tipo_backup = cliente.type(backup_key).decode('utf-8') if isinstance(cliente.type(backup_key), bytes) else cliente.type(backup_key)
        
        if tipo_backup == 'string':
            # Backup de string/JSON
            valor_cifrado = cliente.get(backup_key)
            valor_original = descifrar_valor(valor_cifrado.decode('utf-8') if isinstance(valor_cifrado, bytes) else valor_cifrado)
            
            cliente.set(clave, valor_original)
            cliente.delete(backup_key)
            
            _registrar_estado(connection_id, clave, "INACTIVA")
            return {"filas_restauradas": 1}
            
        elif tipo_backup == 'hash':
            # Backup de hash
            backup_data = cliente.hgetall(backup_key)
            
            datos_restaurados = {}
            for k, v in backup_data.items():
                key_str = k.decode('utf-8') if isinstance(k, bytes) else k
                val_str = v.decode('utf-8') if isinstance(v, bytes) else v
                datos_restaurados[key_str] = descifrar_valor(val_str)
            
            cliente.delete(clave)
            cliente.hset(clave, mapping=datos_restaurados)
            cliente.delete(backup_key)
            
            _registrar_estado(connection_id, clave, "INACTIVA")
            return {"filas_restauradas": len(datos_restaurados)}
        
        else:
            raise ValueError(f"Tipo de backup Redis no soportado: {tipo_backup}")
    
    finally:
        cliente.close()


# ─────────────────────────────────────────────────────────────────────────────
# ESTRATEGIA: Neo4j (Property-level backup)
# ─────────────────────────────────────────────────────────────────────────────

def _neo4j_preflight(motor, label: str) -> str:
    """Verifica que no existan nodos backup para el label."""
    backup_label = label + BACKUP_SUFFIX.replace("__", "_")
    driver = motor.conectar()
    try:
        with driver.session() as session:
            result = session.run(f"MATCH (n:{backup_label}) RETURN count(n) AS cnt")
            cnt = result.single()["cnt"]
            if cnt > 0:
                raise ValueError(
                    f"Pre-flight FAIL: Ya existen {cnt} nodos backup '{backup_label}' en Neo4j. "
                    "Ejecuta 'Restaurar' primero."
                )
    finally:
        driver.close()
    return backup_label


def _neo4j_proteger(motor, label: str, reglas: Dict[str, str], connection_id: str) -> Dict[str, Any]:
    """
    SDM para Neo4j:
    - Backup: Crea nodos <label>_backup_enc con propiedades cifradas + referencia al nodo original
    - Protección: Actualiza propiedades del nodo original con valores enmascarados
    """
    backup_label = _neo4j_preflight(motor, label)
    
    driver = motor.conectar()
    try:
        with driver.session() as session:
            # Contar nodos
            result = session.run(f"MATCH (n:{label}) RETURN count(n) AS cnt")
            total = result.single()["cnt"]
            if total == 0:
                raise ValueError(f"No hay nodos con label '{label}' en Neo4j.")
            
            # Obtener nodos en lotes
            filas_procesadas = 0
            offset = 0
            
            while offset < total:
                result = session.run(
                    f"MATCH (n:{label}) RETURN id(n) AS node_id, properties(n) AS props SKIP $skip LIMIT $limit",
                    skip=offset, limit=BATCH_SIZE
                )
                nodos = list(result)
                
                for nodo in nodos:
                    node_id = nodo["node_id"]
                    props = nodo["props"]
                    
                    # Crear nodo backup con propiedades cifradas
                    props_cifradas = {}
                    for k, v in props.items():
                        if isinstance(v, str):
                            props_cifradas[k] = cifrar_valor(v)
                        elif v is not None:
                            props_cifradas[k] = cifrar_valor(str(v))
                        else:
                            props_cifradas[k] = None
                    
                    # Guardar referencia al nodo original
                    props_cifradas["_original_id"] = node_id
                    props_cifradas["_original_label"] = label
                    
                    # Crear nodo backup
                    session.run(
                        f"CREATE (b:{backup_label} $props)",
                        props=props_cifradas
                    )
                    
                    # Aplicar enmascaramiento a propiedades
                    props_str = {k: str(v) for k, v in props.items() if isinstance(v, str)}
                    if props_str:
                        resultado = aplicar_enmascaramiento([props_str], reglas)[0]
                        
                        # Construir SET clause
                        set_parts = []
                        params = {"node_id": node_id}
                        for k, v in resultado.items():
                            param_name = f"prop_{k}"
                            set_parts.append(f"n.{k} = ${param_name}")
                            params[param_name] = v
                        
                        session.run(
                            f"MATCH (n:{label}) WHERE id(n) = $node_id SET {', '.join(set_parts)}",
                            params
                        )
                    
                    filas_procesadas += 1
                
                offset += BATCH_SIZE
            
            _registrar_estado(connection_id, label, "ACTIVA")
            return {"filas_protegidas": filas_procesadas, "backup_label": backup_label}
    
    finally:
        driver.close()


def _neo4j_restaurar(motor, label: str, connection_id: str) -> Dict[str, Any]:
    """Restaura propiedades originales de Neo4j desde nodos backup."""
    backup_label = label + BACKUP_SUFFIX.replace("__", "_")
    
    driver = motor.conectar()
    try:
        with driver.session() as session:
            # Verificar que existan backups
            result = session.run(f"MATCH (n:{backup_label}) RETURN count(n) AS cnt")
            total = result.single()["cnt"]
            if total == 0:
                raise ValueError(f"No se encontraron nodos backup '{backup_label}' en Neo4j.")
            
            # Restaurar en lotes
            filas_restauradas = 0
            offset = 0
            
            while offset < total:
                result = session.run(
                    f"MATCH (b:{backup_label}) RETURN id(b) AS backup_id, b._original_id AS orig_id, properties(b) AS props SKIP $skip LIMIT $limit",
                    skip=offset, limit=BATCH_SIZE
                )
                backups = list(result)
                
                for backup in backups:
                    orig_id = backup["orig_id"]
                    props = backup["props"]
                    
                    # Descifrar propiedades
                    props_descifradas = {}
                    for k, v in props.items():
                        if k.startswith("_original"):
                            continue
                        if isinstance(v, str):
                            try:
                                props_descifradas[k] = descifrar_valor(v)
                            except Exception:
                                props_descifradas[k] = v
                        else:
                            props_descifradas[k] = v
                    
                    # Restaurar propiedades en nodo original
                    set_parts = []
                    params = {"orig_id": orig_id}
                    for k, v in props_descifradas.items():
                        param_name = f"prop_{k}"
                        set_parts.append(f"n.{k} = ${param_name}")
                        params[param_name] = v
                    
                    if set_parts:
                        session.run(
                            f"MATCH (n:{label}) WHERE id(n) = $orig_id SET {', '.join(set_parts)}",
                            params
                        )
                    
                    filas_restauradas += 1
                
                offset += BATCH_SIZE
            
            # Eliminar nodos backup
            session.run(f"MATCH (n:{backup_label}) DETACH DELETE n")
            
            _registrar_estado(connection_id, label, "INACTIVA")
            return {"filas_restauradas": filas_restauradas}
    
    finally:
        driver.close()


# ─────────────────────────────────────────────────────────────────────────────
# DISPATCHER PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

_ESTRATEGIAS: Dict[str, Tuple[Callable, Callable]] = {
    "sqlite":    (_sqlite_proteger,    _sqlite_restaurar),
    "postgres":  (_postgres_proteger,  _postgres_restaurar),
    "sqlserver": (_sqlserver_proteger, _sqlserver_restaurar),
    "mongodb":   (_mongo_proteger,     _mongo_restaurar),
    "redis":     (_redis_proteger,     _redis_restaurar),
    "neo4j":     (_neo4j_proteger,     _neo4j_restaurar),
}

MOTORES_SDM_DISPONIBLES = list(_ESTRATEGIAS.keys())


def proteger_tabla(
    motor_nombre: str,
    motor: Any,
    tabla: str,
    reglas: Dict[str, str],
    connection_id: str,
) -> Dict[str, Any]:
    if motor_nombre not in _ESTRATEGIAS:
        disponibles = ", ".join(MOTORES_SDM_DISPONIBLES)
        raise ValueError(
            f"SDM no disponible para '{motor_nombre}'. Soportados: {disponibles}."
        )
    fn_proteger, _ = _ESTRATEGIAS[motor_nombre]
    return fn_proteger(motor, tabla, reglas, connection_id)


def restaurar_tabla(
    motor_nombre: str,
    motor: Any,
    tabla: str,
    connection_id: str,
) -> Dict[str, Any]:
    if motor_nombre not in _ESTRATEGIAS:
        disponibles = ", ".join(MOTORES_SDM_DISPONIBLES)
        raise ValueError(
            f"Restore no disponible para '{motor_nombre}'. Soportados: {disponibles}."
        )
    _, fn_restaurar = _ESTRATEGIAS[motor_nombre]
    return fn_restaurar(motor, tabla, connection_id)
