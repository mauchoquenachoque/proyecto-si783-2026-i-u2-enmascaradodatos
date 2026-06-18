import time
from copy import deepcopy
from typing import Callable, Dict, Any, List

from encryption_service import encrypt_value
from masking import aplicar_enmascaramiento

def monitor_overhead(motor_nombre: str, ejecutar_db_func: Callable, reglas: Dict[str, str]) -> Dict[str, Any]:
    """
    Middleware que calcula el overhead comparativo en milisegundos
    para consulta normal, enmascaramiento visual y cifrado simétrico.
    """
    inicio_db = time.perf_counter_ns()
    resultados_db = ejecutar_db_func()
    fin_db = time.perf_counter_ns()
    tiempo_db_ms = (fin_db - inicio_db) / 1_000_000.0

    if not resultados_db:
        return {
            "motor_utilizado": motor_nombre,
            "tiempo_bd_ms": round(tiempo_db_ms, 3),
            "tiempo_normal_ms": round(tiempo_db_ms, 3),
            "tiempo_masked_ms": 0.0,
            "tiempo_encrypted_ms": 0.0,
            "latency_delta_ms": 0.0,
            "cpu_overhead": 0.0,
            "overhead_total_ms": round(tiempo_db_ms, 3),
            "filas_procesadas": 0,
            "masking_mode": "visual_mask",
            "data": []
        }

    datos = deepcopy(resultados_db)
    inicio_mask = time.perf_counter_ns()
    resultados_enmascarados = aplicar_enmascaramiento(deepcopy(datos), reglas or {})
    fin_mask = time.perf_counter_ns()
    tiempo_mask_ms = (fin_mask - inicio_mask) / 1_000_000.0

    inicio_enc = time.perf_counter_ns()
    resultados_encriptados: List[Dict[str, Any]] = deepcopy(datos)
    columnas = list((reglas or {}).keys())
    for fila in resultados_encriptados:
        for columna in columnas:
            if columna in fila and fila[columna] is not None:
                fila[columna] = encrypt_value(fila[columna])
    fin_enc = time.perf_counter_ns()
    tiempo_enc_ms = (fin_enc - inicio_enc) / 1_000_000.0

    overhead_total_ms = tiempo_db_ms + tiempo_mask_ms + tiempo_enc_ms

    return {
        "motor_utilizado": motor_nombre,
        "tiempo_bd_ms": round(tiempo_db_ms, 3),
        "tiempo_normal_ms": round(tiempo_db_ms, 3),
        "tiempo_masked_ms": round(tiempo_mask_ms, 3),
        "tiempo_encrypted_ms": round(tiempo_enc_ms, 3),
        "latency_delta_ms": round(max(tiempo_mask_ms, tiempo_enc_ms) - tiempo_db_ms, 3),
        "cpu_overhead": round(tiempo_mask_ms + tiempo_enc_ms, 3),
        "tiempo_enmascarado_ms": round(tiempo_mask_ms, 3),
        "overhead_total_ms": round(overhead_total_ms, 3),
        "filas_procesadas": len(resultados_enmascarados),
        "masking_mode": "visual_mask",
        "data": resultados_enmascarados
    }
