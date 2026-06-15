"""
main.py — SecOps Universal Monitor API v6.0
Autenticación: email + bcrypt (local) + Google OAuth 2.0
Sesiones persistidas en SQLite (sobrevive reinicios).
Health check completo de bases de datos.
"""

import os
import time
from typing import Any, Dict

import httpx
from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from auth import (agregar_conexion, crear_token_sesion,
                  eliminar_conexion, obtener_conexion, obtener_sesion_actual,
                  revocar_token, limpiar_sesiones_expiradas, obtener_estadisticas_sesiones)
from config import settings
from database_manager import DatabaseFactory
from db_usuarios import (autenticar_usuario, init_db, registrar_usuario,
                         buscar_usuario_por_correo)
import google_oauth
from health_monitor import (ejecutar_health_check_completo,
                           obtener_historial_health, obtener_estadisticas_salud)

load_dotenv()
MASKING_SERVICE_URL = os.getenv("MASKING_SERVICE_URL", "http://localhost:8001")
MONITOR_SERVICE_URL = os.getenv("MONITOR_SERVICE_URL", "http://localhost:8002")
MOTORES_SDM_DISPONIBLES = ["sqlite", "postgres", "sqlserver", "mongodb", "redis", "neo4j"]
_COOKIE_SECURE = os.getenv("RENDER") == "true"

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="SecOps Universal Monitor — Multi-Auth + Multi-DB + Health Check",
    version="6.0.0",
)

# CORS para desarrollo local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static", exist_ok=True)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "api", "version": "6.0.0"}


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Inicializa la BD de usuarios y limpia sesiones expiradas."""
    try:
        init_db()
        limpiar_sesiones_expiradas(dias=30)
    except Exception as exc:
        print(f"[STARTUP] init_db error: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# AUTH — VISTAS HTML
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/login")
async def serve_login():
    return FileResponse("static/login.html")


@app.get("/")
async def serve_dashboard(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    # Verificar que la sesión exista (puede estar en SQLite después de reinicio)
    try:
        sesion = obtener_sesion_actual(request)
    except HTTPException:
        return RedirectResponse(url="/login?error=Sesión+expirada", status_code=status.HTTP_302_FOUND)
    return FileResponse("static/index.html")


# ─────────────────────────────────────────────────────────────────────────────
# AUTH — REGISTRO Y LOGIN TRADICIONAL
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/auth/register", tags=["Auth"])
async def register(payload: Dict[str, Any] = Body(...)):
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

    token = crear_token_sesion(usuario["nombre"], usuario["correo"], "local")
    response = JSONResponse({"message": "Cuenta creada exitosamente.", "nombre": usuario["nombre"]})
    response.set_cookie(
        key="session_token", value=token,
        httponly=True, samesite="lax", secure=_COOKIE_SECURE,
        max_age=30 * 24 * 3600  # 30 días
    )
    return response


@app.post("/api/login", tags=["Auth"])
async def login(correo: str = Form(...), password: str = Form(...)):
    usuario = autenticar_usuario(correo.strip().lower(), password)
    if not usuario:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")

    token = crear_token_sesion(
        usuario["nombre_completo"],
        usuario["correo"],
        usuario.get("proveedor", "local")
    )
    response = JSONResponse({"message": "Login exitoso.", "nombre": usuario["nombre_completo"]})
    response.set_cookie(
        key="session_token", value=token,
        httponly=True, samesite="lax", secure=_COOKIE_SECURE,
        max_age=30 * 24 * 3600
    )
    return response


@app.post("/api/logout", tags=["Auth"])
async def logout(request: Request):
    token = request.cookies.get("session_token")
    if token:
        revocar_token(token)
    response = JSONResponse({"message": "Sesión cerrada."})
    response.delete_cookie("session_token")
    return response


@app.get("/api/auth/me", tags=["Auth"])
async def me(sesion: Dict[str, Any] = Depends(obtener_sesion_actual)):
    return {
        "username": sesion.get("username"),
        "email":    sesion.get("email"),
        "proveedor": sesion.get("proveedor"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# AUTH — GOOGLE OAUTH 2.0
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/auth/google", tags=["Auth Google"])
async def google_login(request: Request):
    """Redirige a Google para autenticación OAuth."""
    if not google_oauth.esta_configurado():
        raise HTTPException(
            status_code=501,
            detail="Google OAuth no configurado. Contacta al administrador."
        )
    
    # Construir redirect URI dinámicamente
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/auth/google/callback"
    
    try:
        url = google_oauth.obtener_url_autenticacion(redirect_uri)
        return RedirectResponse(url=url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/google/callback", tags=["Auth Google"])
async def google_callback(request: Request, code: str = ""):
    """Callback de Google OAuth. Procesa el código y crea la sesión."""
    if not code:
        return RedirectResponse(url="/login?error=No+se+recibió+código+de+autorización")
    
    # Construir redirect URI (debe coincidir con el usado en el login)
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/auth/google/callback"
    
    try:
        user_data = await google_oauth.procesar_callback_google(code, redirect_uri)
        email = user_data["email"]
        nombre = user_data["nombre"]
        
        # Verificar si el usuario ya existe
        usuario_existente = buscar_usuario_por_correo(email)
        
        if not usuario_existente:
            # Registrar nuevo usuario de Google
            try:
                registrar_usuario(nombre, email, password="", proveedor="google")
            except ValueError:
                pass  # Ya existe, continuar
        
        # Crear sesión
        token = crear_token_sesion(nombre, email, "google")
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key="session_token", value=token,
            httponly=True, samesite="lax", secure=_COOKIE_SECURE,
            max_age=30 * 24 * 3600
        )
        return response
        
    except Exception as e:
        error_msg = str(e).replace(" ", "+")
        return RedirectResponse(url=f"/login?error=Error+con+Google:+{error_msg}")


@app.get("/api/auth/google/status", tags=["Auth Google"])
async def google_status():
    """Retorna si Google OAuth está configurado."""
    return {
        "configurado": google_oauth.esta_configurado(),
        "client_id": google_oauth.GOOGLE_CLIENT_ID[:20] + "..." if google_oauth.GOOGLE_CLIENT_ID else None
    }


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH CHECK DE BASES DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/health/databases", tags=["Health Monitor"])
async def health_databases():
    """Ejecuta health check completo de todas las BDs y servicios."""
    return await ejecutar_health_check_completo()


@app.get("/api/health/history", tags=["Health Monitor"])
async def health_history(servicio: str = None, limite: int = 50):
    """Obtiene historial de health checks."""
    return await obtener_historial_health(servicio, limite)


@app.get("/api/health/stats", tags=["Health Monitor"])
async def health_stats():
    """Obtiene estadísticas agregadas de salud."""
    return await obtener_estadisticas_salud()


@app.get("/api/sessions/stats", tags=["Auth"])
async def session_stats():
    """Retorna estadísticas de sesiones (solo para debug/admin)."""
    return obtener_estadisticas_sesiones()


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

    motor = DatabaseFactory.obtener_motor(motor_nombre, credenciales)
    query, kwargs_extra = "", {}

    if motor_nombre in ("postgres", "mysql", "sqlserver", "sqlite"):
        query = f"SELECT TOP 100 * FROM {tabla}" if motor_nombre == "sqlserver" else f"SELECT * FROM {tabla} LIMIT 100"
    elif motor_nombre == "mongodb":
        query = {}; kwargs_extra["coleccion"] = tabla
    elif motor_nombre == "neo4j":
        query = f"MATCH (n:{tabla}) RETURN n LIMIT 100"
    elif motor_nombre == "redis":
        kwargs_extra["tipo_comando"] = "get"; query = tabla

    try:
        inicio_db = time.perf_counter_ns()
        resultados_db = motor.ejecutar_consulta(query, **kwargs_extra)
        fin_db = time.perf_counter_ns()
        tiempo_db_ms = (fin_db - inicio_db) / 1_000_000.0

        tiempo_mask_ms = 0.0
        data_final = resultados_db or []

        if resultados_db and reglas:
            async with httpx.AsyncClient() as client:
                try:
                    from fastapi.encoders import jsonable_encoder
                    payload_json = jsonable_encoder({"datos": resultados_db, "reglas": reglas})
                    res = await client.post(
                        f"{MASKING_SERVICE_URL}/mask",
                        json=payload_json,
                        timeout=10.0
                    )
                    if res.status_code == 200:
                        res_json = res.json()
                        data_final = res_json.get("datos_enmascarados", [])
                        tiempo_mask_ms = res_json.get("tiempo_mask_ms", 0.0)
                    else:
                        raise Exception(f"Error del servicio de masking: {res.text}")
                except Exception as e:
                    raise HTTPException(status_code=502, detail=f"Fallo comunicación con Masking Service: {str(e)}")

        overhead_total_ms = tiempo_db_ms + tiempo_mask_ms
        metrics_payload = {
            "motor_utilizado": motor_nombre,
            "tiempo_bd_ms": round(tiempo_db_ms, 3),
            "tiempo_mask_ms": round(tiempo_mask_ms, 3),
            "overhead_total_ms": round(overhead_total_ms, 3),
            "filas_procesadas": len(data_final)
        }

        async with httpx.AsyncClient() as client:
            try:
                await client.post(f"{MONITOR_SERVICE_URL}/metrics", json=metrics_payload, timeout=2.0)
            except Exception as e:
                print(f"[GATEWAY] Advertencia: No se pudieron enviar métricas: {e}")

        return {
            "motor_utilizado": motor_nombre,
            "tiempo_bd_ms": round(tiempo_db_ms, 3),
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
