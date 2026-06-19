"""
main.py — SecOps Universal Monitor API v5.0
Autenticación: email + bcrypt (local) + Google OAuth2.
"""

import os
import time
from datetime import datetime, timezone
from typing import Any, Dict

import httpx
from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from auth import (SESIONES_ACTIVAS, agregar_conexion, crear_token_sesion,
                  eliminar_conexion, obtener_conexion, obtener_sesion_actual,
                  revocar_token)
from config import settings
from database_health import check_database_health_batch
from database_manager import DatabaseFactory
from db_usuarios import (autenticar_usuario, init_db, registrar_usuario)
from oauth_google import oauth, get_google_user_info

load_dotenv()
API_SERVICE_URL = os.getenv("API_SERVICE_URL", "http://localhost:8000")
MASKING_SERVICE_URL = os.getenv("MASKING_SERVICE_URL", "http://localhost:8001")
MONITOR_SERVICE_URL = os.getenv("MONITOR_SERVICE_URL", "http://localhost:8002")
MOTORES_SDM_DISPONIBLES = ["sqlite", "postgres", "sqlserver", "mongodb", "mysql", "mariadb"]
# Render sirve HTTPS; las cookies deben marcarse secure en produccion
_COOKIE_SECURE = os.getenv("RENDER") == "true"


async def _call_masking_service(path: str, payload: Dict[str, Any], method: str = "POST", timeout: float = 10.0):
    async with httpx.AsyncClient() as client:
        response = await client.request(method, f"{MASKING_SERVICE_URL}{path}", json=payload, timeout=timeout)
        if response.status_code >= 400:
            detail_msg = response.json().get("detail", response.text) if response.headers.get("content-type") == "application/json" else response.text
            raise HTTPException(status_code=response.status_code, detail=detail_msg)
        return response.json()


async def _probe_service(name: str, url: str) -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        if not url:
            raise ValueError("URL is empty")
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url.rstrip("/") + "/health")
            response.raise_for_status()
        status_value = "UP"
        error = None
    except Exception as exc:
        status_value = "DOWN"
        error = str(exc)
    result = {
        "service": name,
        "status": status_value,
        "response_time_ms": round((time.perf_counter() - started) * 1000, 3),
    }
    if error:
        result["error"] = error
    return result

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="SecOps Universal Monitor — Autenticación Real + Multi-DB",
    version="5.0.0",
)

# Middleware de sesión para OAuth2
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", os.urandom(32).hex()))

os.makedirs("static", exist_ok=True)


# Global exception handlers to save logs in monitor service
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_payload = {
        "service": "api",
        "error_type": type(exc).__name__,
        "message": str(exc),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{MONITOR_SERVICE_URL}/errors", json=error_payload, timeout=2.0)
    except Exception:
        pass
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code >= 400:
        error_payload = {
            "service": "api",
            "error_type": "HTTPException",
            "message": f"Status {exc.status_code}: {exc.detail}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{MONITOR_SERVICE_URL}/errors", json=error_payload, timeout=2.0)
        except Exception:
            pass
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.get("/health", tags=["Health"])
async def health():
    try:
        masking_status = await _probe_service("masking_service", MASKING_SERVICE_URL)
    except Exception as exc:
        masking_status = {"service": "masking_service", "status": "DOWN", "error": str(exc)}

    try:
        monitor_status = await _probe_service("monitor_service", MONITOR_SERVICE_URL)
    except Exception as exc:
        monitor_status = {"service": "monitor_service", "status": "DOWN", "error": str(exc)}

    return {
        "status": "ok",
        "api": "UP",
        "masking_service": masking_status.get("status", "DOWN"),
        "monitor_service": monitor_status.get("status", "DOWN"),
        "details": {
            "api": {"status": "UP"},
            "masking_service": masking_status,
            "monitor_service": monitor_status,
        },
    }


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Inicializa la BD de usuarios sin bloquear el health check de Render."""
    try:
        init_db()
    except Exception as exc:
        print(f"[STARTUP] init_db error (la app sigue arrancando): {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# AUTH — VISTAS HTML
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/login")
async def serve_login():
    return FileResponse("static/login.html")


@app.get("/")
async def serve_dashboard(request: Request):
    token = request.cookies.get("session_token")
    if not token or token not in SESIONES_ACTIVAS:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return FileResponse("static/index.html")


# ─────────────────────────────────────────────────────────────────────────────
# AUTH — REGISTRO Y LOGIN TRADICIONAL
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/auth/register", tags=["Auth"])
async def register(payload: Dict[str, Any] = Body(...)):
    """
    Registra un nuevo usuario con email + contraseña.
    Body: { nombre, correo, password }
    """
    nombre   = (payload.get("nombre") or "").strip()
    correo   = (payload.get("correo") or "").strip().lower()
    password = payload.get("password") or ""

    if not nombre or not correo or not password:
        raise HTTPException(status_code=400, detail="Nombre, correo y contraseña son obligatorios.")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres.")

    try:
        usuario = registrar_usuario(nombre, correo, password)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Auto-login tras registro exitoso
    token = crear_token_sesion(usuario["nombre"], usuario["correo"], "local")
    response = JSONResponse({"message": "Cuenta creada exitosamente.", "nombre": usuario["nombre"]})
    response.set_cookie(key="session_token", value=token, httponly=True, samesite="lax", secure=_COOKIE_SECURE)
    return response


@app.post("/api/login", tags=["Auth"])
async def login(correo: str = Form(...), password: str = Form(...)):
    usuario = autenticar_usuario(correo.strip().lower(), password)
    if not usuario:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")

    token = crear_token_sesion(usuario["nombre_completo"], usuario["correo"], usuario.get("proveedor","local"))
    response = JSONResponse({"message": "Login exitoso.", "nombre": usuario["nombre_completo"]})
    response.set_cookie(key="session_token", value=token, httponly=True, samesite="lax", secure=_COOKIE_SECURE)
    return response


@app.post("/api/logout", tags=["Auth"])
async def logout(request: Request):
    token = request.cookies.get("session_token")
    if token:
        revocar_token(token)
    response = JSONResponse({"message": "Sesión cerrada."})
    response.delete_cookie("session_token")
    return response


# ─────────────────────────────────────────────────────────────────────────────
# AUTH — GOOGLE OAUTH2
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/auth/google/login", tags=["Auth"])
async def google_login(request: Request):
    """Redirige al usuario a Google para autenticación."""
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/google/callback", tags=["Auth"])
async def google_callback(request: Request):
    """Callback de Google después de la autenticación."""
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en autenticación Google: {str(e)}")
    
    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(status_code=400, detail="No se pudo obtener información del usuario de Google.")
    
    nombre = user_info.get('name', 'Usuario Google')
    correo = user_info.get('email', '')
    
    if not correo:
        raise HTTPException(status_code=400, detail="No se pudo obtener el correo de Google.")
    
    # Registrar usuario si no existe (auto-registro con Google)
    try:
        registrar_usuario(nombre, correo, os.urandom(16).hex(), proveedor="google")
    except ValueError:
        pass  # El usuario ya existe, continuar
    
    # Crear sesión
    session_token = crear_token_sesion(nombre, correo, "google")
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="session_token", value=session_token, httponly=True, samesite="lax", secure=_COOKIE_SECURE)
    return response


@app.get("/api/auth/google/url", tags=["Auth"])
async def get_google_auth_url():
    """Retorna la URL de autorización de Google."""
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
    return {"url": f"https://accounts.google.com/o/oauth2/v2/auth?client_id={os.getenv('GOOGLE_CLIENT_ID')}&redirect_uri={redirect_uri}&response_type=code&scope=openid+email+profile"}


@app.get("/api/auth/me", tags=["Auth"])
async def me(sesion: Dict[str, Any] = Depends(obtener_sesion_actual)):
    """Retorna los datos del usuario de la sesión activa."""
    return {
        "username": sesion.get("username"),
        "email":    sesion.get("email"),
        "proveedor": sesion.get("proveedor"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# CONEXIONES MÚLTIPLES
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v1/connect", tags=["SecOps Universal"])
async def conectar_db(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    sesion: Dict[str, Any] = Depends(obtener_sesion_actual),
):
    motor_nombre = payload.get("motor")
    credenciales = payload.get("credenciales", {})
    alias = payload.get("alias", f"{str(motor_nombre).capitalize()} DB")
    try:
        motor = DatabaseFactory.obtener_motor(motor_nombre, credenciales)
        esquema = motor.obtener_esquema()
        payload["esquema_cache"] = esquema
        payload["alias"] = alias
        conn_id = agregar_conexion(request, payload)
        return {"message": "Conexión exitosa", "connection_id": conn_id, "alias": alias, "esquema": esquema}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error conectando a BD: {str(e)}")


@app.get("/api/v1/connections", tags=["SecOps Universal"])
async def get_connections(sesion: Dict[str, Any] = Depends(obtener_sesion_actual)):
    conexiones = sesion.get("conexiones", {})
    return {"conexiones": [{"id": cid, "alias": d.get("alias"), "motor": d.get("motor")} for cid, d in conexiones.items()]}


@app.delete("/api/v1/connections/{connection_id}", tags=["SecOps Universal"])
async def delete_connection(connection_id: str, request: Request, sesion: Dict[str, Any] = Depends(obtener_sesion_actual)):
    eliminar_conexion(request, connection_id)
    return {"message": "Conexión eliminada"}


@app.get("/api/v1/schema", tags=["SecOps Universal"])
async def get_schema(connection_id: str, request: Request):
    config = obtener_conexion(request, connection_id)
    return config.get("esquema_cache", {"tablas": {}})


@app.post("/api/v1/execute_test", tags=["SecOps Universal"])
async def ejecutar_test(request: Request, payload: Dict[str, Any] = Body(...)):
    connection_id = payload.get("connection_id")
    if not connection_id:
        raise HTTPException(status_code=400, detail="Falta connection_id.")

    config = obtener_conexion(request, connection_id)
    motor_nombre = config.get("motor")
    credenciales = config.get("credenciales")
    tabla = payload.get("tabla")
    reglas = payload.get("reglas", {})

    if not tabla:
        raise HTTPException(status_code=400, detail="Especifica la tabla a consultar.")

    try:
        benchmark_payload = {
            "motor_nombre": motor_nombre,
            "credenciales": credenciales,
            "tabla": tabla,
            "reglas": reglas,
            "limit": 100,
        }
        resultado = await _call_masking_service("/benchmark", benchmark_payload, method="POST", timeout=30.0)

        data_final = resultado.get("datos_enmascarados", [])
        tiempo_normal_ms = float(resultado.get("tiempo_normal_ms", 0.0))
        tiempo_mask_ms = float(resultado.get("tiempo_masked_ms", 0.0))
        tiempo_encrypted_ms = float(resultado.get("tiempo_encrypted_ms", 0.0))
        latency_delta_ms = float(resultado.get("latency_delta_ms", 0.0))
        cpu_overhead = float(resultado.get("cpu_overhead", 0.0))
        overhead_total_ms = tiempo_normal_ms + tiempo_mask_ms + tiempo_encrypted_ms

        metrics_payload = {
            "motor_utilizado": motor_nombre,
            "masking_mode": resultado.get("masking_mode", "visual_mask"),
            "tiempo_normal_ms": round(tiempo_normal_ms, 3),
            "tiempo_masked_ms": round(tiempo_mask_ms, 3),
            "tiempo_encrypted_ms": round(tiempo_encrypted_ms, 3),
            "latency_delta_ms": round(latency_delta_ms, 3),
            "cpu_overhead": round(cpu_overhead, 3),
            "tiempo_bd_ms": round(tiempo_normal_ms, 3),
            "tiempo_mask_ms": round(tiempo_mask_ms, 3),
            "overhead_total_ms": round(overhead_total_ms, 3),
            "filas_procesadas": len(data_final)
        }

        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{MONITOR_SERVICE_URL}/metrics",
                    json=metrics_payload,
                    timeout=2.0
                )
                algorithm_metrics = resultado.get("algorithm_metrics", [])
                if algorithm_metrics:
                    await client.post(
                        f"{MONITOR_SERVICE_URL}/algorithm-metrics",
                        json={"metrics": algorithm_metrics},
                        timeout=2.0,
                    )
            except Exception as e:
                print(f"[GATEWAY] Advertencia: No se pudieron enviar métricas al Monitor Service: {e}")

        # Formato de retorno exacto esperado por el frontend
        return {
            "motor_utilizado": motor_nombre,
            "masking_mode": resultado.get("masking_mode", "visual_mask"),
            "tiempo_normal_ms": round(tiempo_normal_ms, 3),
            "tiempo_masked_ms": round(tiempo_mask_ms, 3),
            "tiempo_encrypted_ms": round(tiempo_encrypted_ms, 3),
            "latency_delta_ms": round(latency_delta_ms, 3),
            "cpu_overhead": round(cpu_overhead, 3),
            "tiempo_bd_ms": round(tiempo_normal_ms, 3),
            "tiempo_enmascarado_ms": round(tiempo_mask_ms, 3),
            "overhead_total_ms": round(overhead_total_ms, 3),
            "filas_procesadas": len(data_final),
            "data": data_final
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# GOBERNANZA SDM
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v1/governance/protect", tags=["Gobernanza SDM"])
async def activar_proteccion(request: Request, payload: Dict[str, Any] = Body(...)):
    connection_id = payload.get("connection_id")
    tabla = payload.get("tabla")
    reglas = payload.get("reglas", {})
    if not connection_id or not tabla:
        raise HTTPException(status_code=400, detail="Faltan connection_id y/o tabla.")
    if not reglas:
        raise HTTPException(status_code=400, detail="Define al menos una regla.")

    config = obtener_conexion(request, connection_id)
    motor_nombre = config.get("motor")
    if motor_nombre not in MOTORES_SDM_DISPONIBLES:
        raise HTTPException(
            status_code=400,
            detail=f"SDM no disponible para '{motor_nombre}'. Soportados: {', '.join(MOTORES_SDM_DISPONIBLES)}."
        )

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                f"{MASKING_SERVICE_URL}/protect",
                json={
                    "motor_nombre": motor_nombre,
                    "credenciales": config.get("credenciales"),
                    "tabla": tabla,
                    "reglas": reglas,
                    "connection_id": connection_id
                },
                timeout=30.0
            )
            if res.status_code == 200:
                resultado = res.json()
                return {"estado": "ACTIVA", "mensaje": f"SDM activado en '{tabla}'.", **resultado}
            elif res.status_code == 409:
                raise HTTPException(status_code=409, detail=res.json().get("detail", "Conflicto en pre-flight"))
            else:
                detail_msg = res.json().get("detail", res.text) if res.headers.get("content-type") == "application/json" else res.text
                raise HTTPException(status_code=res.status_code, detail=detail_msg)
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Fallo comunicación con Masking Service: {str(e)}")


@app.post("/api/v1/governance/restore", tags=["Gobernanza SDM"])
async def revertir_proteccion(request: Request, payload: Dict[str, Any] = Body(...)):
    connection_id = payload.get("connection_id")
    tabla = payload.get("tabla")
    if not connection_id or not tabla:
        raise HTTPException(status_code=400, detail="Faltan connection_id y/o tabla.")

    config = obtener_conexion(request, connection_id)
    motor_nombre = config.get("motor")

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                f"{MASKING_SERVICE_URL}/restore",
                json={
                    "motor_nombre": motor_nombre,
                    "credenciales": config.get("credenciales"),
                    "tabla": tabla,
                    "connection_id": connection_id
                },
                timeout=30.0
            )
            if res.status_code == 200:
                resultado = res.json()
                return {"estado": "INACTIVA", "mensaje": f"Datos restaurados en '{tabla}'.", **resultado}
            elif res.status_code == 409:
                raise HTTPException(status_code=409, detail=res.json().get("detail", "Conflicto en restauración"))
            else:
                detail_msg = res.json().get("detail", res.text) if res.headers.get("content-type") == "application/json" else res.text
                raise HTTPException(status_code=res.status_code, detail=detail_msg)
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Fallo comunicación con Masking Service: {str(e)}")


@app.get("/api/v1/governance/status", tags=["Gobernanza SDM"])
async def estado_gobernanza(connection_id: str, tabla: str, request: Request):
    config = obtener_conexion(request, connection_id)

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                f"{MASKING_SERVICE_URL}/status",
                json={
                    "connection_id": connection_id,
                    "tabla": tabla,
                    "motor_nombre": config.get("motor"),
                    "credenciales": config.get("credenciales")
                },
                timeout=5.0
            )
            if res.status_code == 200:
                return res.json()
            else:
                detail_msg = res.json().get("detail", res.text) if res.headers.get("content-type") == "application/json" else res.text
                raise HTTPException(status_code=res.status_code, detail=detail_msg)
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Fallo comunicación con Masking Service: {str(e)}")


@app.get("/api/v1/monitor/system", tags=["Monitor"])
async def monitor_system():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{MONITOR_SERVICE_URL}/system/metrics", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Fallo comunicando con Monitor Service: {str(e)}")


@app.get("/api/v1/monitor/services", tags=["Monitor"])
async def monitor_services():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{MONITOR_SERVICE_URL}/service-health", json={}, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Fallo comunicando con Monitor Service: {str(e)}")


@app.get("/api/v1/monitor/databases", tags=["Monitor"])
async def monitor_databases(request: Request, sesion: Dict[str, Any] = Depends(obtener_sesion_actual)):
    """Verifica la salud de todas las conexiones activas en sesión.
    Primero intenta vía monitor_service; si está caído, hace el check directamente."""
    conexiones = list((sesion.get("conexiones") or {}).values())

    # Intentar via monitor_service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MONITOR_SERVICE_URL}/db-health",
                json={"connections": conexiones},
                timeout=15.0,
            )
            response.raise_for_status()
            return response.json()
    except Exception:
        pass  # Monitor service no disponible, usamos fallback directo

    # Fallback directo: check sin depender del monitor_service
    try:
        results = check_database_health_batch(conexiones)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al verificar salud de bases de datos: {str(e)}")


@app.get("/api/v1/monitor/algorithms", tags=["Monitor"])
async def monitor_algorithms():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{MONITOR_SERVICE_URL}/algorithm-ranking", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Fallo comunicando con Monitor Service: {str(e)}")


@app.get("/api/v1/monitor/engine-stats", tags=["Monitor"])
async def monitor_engine_stats():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{MONITOR_SERVICE_URL}/engine-stats", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Fallo comunicando con Monitor Service: {str(e)}")


@app.get("/api/v1/monitor/errors", tags=["Monitor"])
async def monitor_errors(limit: int = 50):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{MONITOR_SERVICE_URL}/errors", params={"limit": limit}, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Fallo comunicando con Monitor Service: {str(e)}")


@app.post("/api/v1/monitor/errors", tags=["Monitor"])
async def monitor_save_error(payload: Dict[str, Any] = Body(...)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{MONITOR_SERVICE_URL}/errors", json=payload, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Fallo comunicando con Monitor Service: {str(e)}")


@app.get("/mask/preview", tags=["Masking Académico"])
async def mask_preview(request: Request, payload: Dict[str, Any] = Body(...)):
    connection_id = payload.get("connection_id")
    if not connection_id:
        raise HTTPException(status_code=400, detail="Falta connection_id.")
    config = obtener_conexion(request, connection_id)
    tabla = payload.get("table") or payload.get("tabla")
    columna = payload.get("column") or payload.get("columna")
    if not tabla or not columna:
        raise HTTPException(status_code=400, detail="Faltan table/tabla y column/columna.")
    return await _call_masking_service("/mask/preview", {
        "motor_nombre": config.get("motor"),
        "credenciales": config.get("credenciales"),
        "tabla": tabla,
        "column": columna,
        "mask_type": payload.get("mask_type", "generic"),
    }, method="GET", timeout=10.0)


@app.get("/mask/view", tags=["Masking Académico"])
async def mask_view(request: Request, payload: Dict[str, Any] = Body(...)):
    connection_id = payload.get("connection_id")
    if not connection_id:
        raise HTTPException(status_code=400, detail="Falta connection_id.")
    config = obtener_conexion(request, connection_id)
    tabla = payload.get("table") or payload.get("tabla")
    columna = payload.get("column") or payload.get("columna")
    if not tabla or not columna:
        raise HTTPException(status_code=400, detail="Faltan table/tabla y column/columna.")
    return await _call_masking_service("/mask/view", {
        "motor_nombre": config.get("motor"),
        "credenciales": config.get("credenciales"),
        "tabla": tabla,
        "column": columna,
        "mask_type": payload.get("mask_type", "generic"),
        "limit": payload.get("limit", 20),
    }, method="GET", timeout=10.0)


@app.post("/encrypt", tags=["Cifrado"])
async def encrypt(request: Request, payload: Dict[str, Any] = Body(...)):
    connection_id = payload.get("connection_id")
    if not connection_id:
        raise HTTPException(status_code=400, detail="Falta connection_id.")
    config = obtener_conexion(request, connection_id)
    tabla = payload.get("table") or payload.get("tabla")
    columna = payload.get("column") or payload.get("columna")
    if not tabla or not columna:
        raise HTTPException(status_code=400, detail="Faltan table/tabla y column/columna.")
    return await _call_masking_service("/encrypt", {
        "motor_nombre": config.get("motor"),
        "credenciales": config.get("credenciales"),
        "tabla": tabla,
        "column": columna,
    }, method="POST", timeout=30.0)


@app.post("/decrypt", tags=["Cifrado"])
async def decrypt(request: Request, payload: Dict[str, Any] = Body(...)):
    connection_id = payload.get("connection_id")
    if not connection_id:
        raise HTTPException(status_code=400, detail="Falta connection_id.")
    config = obtener_conexion(request, connection_id)
    tabla = payload.get("table") or payload.get("tabla")
    columna = payload.get("column") or payload.get("columna")
    if not tabla or not columna:
        raise HTTPException(status_code=400, detail="Faltan table/tabla y column/columna.")
    return await _call_masking_service("/decrypt", {
        "motor_nombre": config.get("motor"),
        "credenciales": config.get("credenciales"),
        "tabla": tabla,
        "column": columna,
    }, method="POST", timeout=30.0)


@app.get("/api/v1/monitor/metrics", tags=["Monitor"])
async def monitor_metrics():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{MONITOR_SERVICE_URL}/metrics", timeout=5.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Fallo comunicando con Monitor Service: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

