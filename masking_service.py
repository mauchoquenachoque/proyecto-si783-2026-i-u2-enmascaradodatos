from copy import deepcopy
import time
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, Body

from database_manager import DatabaseFactory, obtener_filas_tabla, obtener_valor_ejemplo, transformar_columna_tabla
from encryption_service import encrypt_value, decrypt_value
from governance import proteger_tabla, restaurar_tabla, obtener_estado
from masking import academic_mask_value, aplicar_enmascaramiento

app = FastAPI(title="SecOps Masking Service")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "masking"}


def _build_motor(payload: Dict[str, Any]):
    motor_nombre = payload.get("motor_nombre")
    credenciales = payload.get("credenciales")
    if not motor_nombre or not credenciales:
        raise HTTPException(status_code=400, detail="Faltan motor_nombre y/o credenciales.")
    return DatabaseFactory.obtener_motor(motor_nombre, credenciales)


def _resolve_column_payload(payload: Dict[str, Any]) -> tuple[str, str]:
    tabla = payload.get("tabla") or payload.get("table")
    columna = payload.get("column") or payload.get("columna")
    if not tabla or not columna:
        raise HTTPException(status_code=400, detail="Faltan tabla y/o columna.")
    return tabla, columna


def _mask_rows(rows: List[Dict[str, Any]], reglas: Dict[str, str]) -> List[Dict[str, Any]]:
    if not rows:
        return []
    return aplicar_enmascaramiento(deepcopy(rows), reglas or {})


def _encrypt_rows(rows: List[Dict[str, Any]], reglas: Dict[str, str]) -> List[Dict[str, Any]]:
    if not rows:
        return []
    resultado = deepcopy(rows)
    columnas = list((reglas or {}).keys())
    for fila in resultado:
        for columna in columnas:
            if columna in fila and fila[columna] is not None:
                fila[columna] = encrypt_value(fila[columna])
    return resultado


@app.get("/mask/preview")
async def mask_preview(payload: Dict[str, Any] = Body(...)):
    motor = _build_motor(payload)
    tabla, columna = _resolve_column_payload(payload)
    mask_type = payload.get("mask_type", "generic")

    original = obtener_valor_ejemplo(motor, tabla, columna)
    if original is None:
        raise HTTPException(status_code=404, detail="No se encontró un valor de ejemplo para la columna solicitada.")

    return {
        "original": original,
        "masked": academic_mask_value(original, mask_type),
        "mask_type": mask_type,
    }


@app.get("/mask/view")
async def mask_view(payload: Dict[str, Any] = Body(...)):
    motor = _build_motor(payload)
    tabla, columna = _resolve_column_payload(payload)
    mask_type = payload.get("mask_type", "generic")

    filas = obtener_filas_tabla(motor, tabla, limite=int(payload.get("limit", 20)))
    vista = []
    clave_real = f"{columna}_real" if columna.lower().startswith("nombre") or mask_type == "name" else "original"
    clave_mask = f"{columna}_mask" if columna.lower().startswith("nombre") or mask_type == "name" else "masked"

    for fila in filas:
        valor = fila.get(columna)
        if valor is None:
            continue
        vista.append({clave_real: valor, clave_mask: academic_mask_value(valor, mask_type)})

    return vista


@app.post("/benchmark")
async def benchmark(payload: Dict[str, Any] = Body(...)):
    motor = _build_motor(payload)
    tabla = payload.get("tabla") or payload.get("table")
    reglas = payload.get("reglas", {})
    if not tabla:
        raise HTTPException(status_code=400, detail="Falta tabla.")

    inicio_db = time.perf_counter_ns()
    datos = obtener_filas_tabla(motor, tabla, limite=int(payload.get("limit", 100)))
    fin_db = time.perf_counter_ns()
    tiempo_normal_ms = (fin_db - inicio_db) / 1_000_000.0

    inicio_mask = time.perf_counter_ns()
    datos_enmascarados = _mask_rows(datos, reglas)
    fin_mask = time.perf_counter_ns()
    tiempo_masked_ms = (fin_mask - inicio_mask) / 1_000_000.0

    inicio_enc = time.perf_counter_ns()
    datos_encriptados = _encrypt_rows(datos, reglas)
    fin_enc = time.perf_counter_ns()
    tiempo_encrypted_ms = (fin_enc - inicio_enc) / 1_000_000.0

    algorithm_metrics = []
    for algoritmo in ["redaccion", "hashing", "encriptacion", "fpe"]:
        reglas_algoritmo = {columna: regla for columna, regla in (reglas or {}).items() if regla == algoritmo}
        if not reglas_algoritmo:
            continue
        inicio_algo = time.perf_counter_ns()
        _ = _mask_rows(datos, reglas_algoritmo)
        fin_algo = time.perf_counter_ns()
        algorithm_metrics.append({
            "algorithm": algoritmo,
            "columns_masked": len(reglas_algoritmo),
            "rows_processed": len(datos),
            "execution_time_ms": round((fin_algo - inicio_algo) / 1_000_000.0, 3),
        })

    latency_delta_ms = max(tiempo_masked_ms, tiempo_encrypted_ms) - tiempo_normal_ms
    cpu_overhead = tiempo_masked_ms + tiempo_encrypted_ms

    return {
        "motor_utilizado": payload.get("motor_nombre"),
        "masking_mode": "visual_mask",
        "tiempo_normal_ms": round(tiempo_normal_ms, 3),
        "tiempo_masked_ms": round(tiempo_masked_ms, 3),
        "tiempo_encrypted_ms": round(tiempo_encrypted_ms, 3),
        "latency_delta_ms": round(latency_delta_ms, 3),
        "cpu_overhead": round(cpu_overhead, 3),
        "filas_procesadas": len(datos),
        "datos_enmascarados": datos_enmascarados,
        "datos_encriptados": datos_encriptados,
        "algorithm_metrics": algorithm_metrics,
    }

@app.post("/protect")
async def protect(payload: Dict[str, Any] = Body(...)):
    motor_nombre = payload.get("motor_nombre")
    credenciales = payload.get("credenciales")
    tabla = payload.get("tabla")
    reglas = payload.get("reglas")
    connection_id = payload.get("connection_id")
    
    try:
        motor = DatabaseFactory.obtener_motor(motor_nombre, credenciales)
        resultado = proteger_tabla(motor_nombre, motor, tabla, reglas, connection_id)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/restore")
async def restore(payload: Dict[str, Any] = Body(...)):
    motor_nombre = payload.get("motor_nombre")
    credenciales = payload.get("credenciales")
    tabla = payload.get("tabla")
    connection_id = payload.get("connection_id")
    
    try:
        motor = DatabaseFactory.obtener_motor(motor_nombre, credenciales)
        resultado = restaurar_tabla(motor_nombre, motor, tabla, connection_id)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mask")
async def mask(payload: Dict[str, Any] = Body(...)):
    resultado = await benchmark({
        "motor_nombre": payload.get("motor_nombre"),
        "credenciales": payload.get("credenciales"),
        "tabla": payload.get("tabla"),
        "reglas": payload.get("reglas", {}),
        "limit": payload.get("limit", 100),
    })
    return {
        "datos_enmascarados": resultado.get("datos_enmascarados", []),
        "tiempo_mask_ms": resultado.get("tiempo_masked_ms", 0.0),
    }


@app.post("/encrypt")
async def encrypt(payload: Dict[str, Any] = Body(...)):
    try:
        motor = _build_motor(payload)
        tabla, columna = _resolve_column_payload(payload)
        filas_afectadas = transformar_columna_tabla(motor, tabla, columna, encrypt_value)
        return {"rows_updated": filas_afectadas, "masking_mode": "encryption"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al encriptar: {str(e)}")


@app.post("/decrypt")
async def decrypt(payload: Dict[str, Any] = Body(...)):
    try:
        motor = _build_motor(payload)
        tabla, columna = _resolve_column_payload(payload)
        filas_afectadas = transformar_columna_tabla(motor, tabla, columna, decrypt_value)
        return {"rows_updated": filas_afectadas, "masking_mode": "encryption"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al desencriptar: {str(e)}")

@app.post("/status")
async def status(payload: Dict[str, Any] = Body(...)):
    connection_id = payload.get("connection_id")
    tabla = payload.get("tabla")
    motor_nombre = payload.get("motor_nombre")
    credenciales = payload.get("credenciales")
    
    try:
        estado = obtener_estado(connection_id, tabla)
        
        # Auto-sanación: si figura INACTIVA pero la tabla de backup física existe,
        # retornamos ACTIVA para habilitar el botón de restauración en el frontend.
        if estado == "INACTIVA" and motor_nombre and credenciales:
            try:
                motor = DatabaseFactory.obtener_motor(motor_nombre, credenciales)
                backup = tabla + "__raw"
                existe = False
                
                if motor_nombre == "sqlite":
                    res = motor.ejecutar_consulta(
                        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{backup}'"
                    )
                    existe = len(res) > 0
                elif motor_nombre in ["mysql", "mariadb"]:
                    res = motor.ejecutar_consulta(f"SHOW TABLES LIKE '{backup}'")
                    existe = res and len(res) > 0
                elif motor_nombre == "postgres":
                    res = motor.ejecutar_consulta(f"SELECT to_regclass('public.\"{backup}\"') AS existe")
                    existe = len(res) > 0 and res[0].get("existe") is not None
                elif motor_nombre == "sqlserver":
                    res = motor.ejecutar_consulta(f"SELECT OBJECT_ID('{backup}', 'U') AS existe")
                    existe = len(res) > 0 and res[0].get("existe") is not None
                elif motor_nombre == "mongodb":
                    cliente = motor.conectar()
                    db_name = motor.credenciales.get("database")
                    db = cliente[db_name]
                    existe = backup in db.list_collection_names()
                    cliente.close()
                    
                if existe:
                    estado = "ACTIVA"
            except Exception:
                pass
                
        return {"connection_id": connection_id, "tabla": tabla, "estado": estado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("masking_service:app", host="0.0.0.0", port=8001)
