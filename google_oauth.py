"""
google_oauth.py — Autenticación con Google OAuth 2.0
Maneja el flujo de autorización con Google.

CONFIGURACIÓN REQUERIDA:
1. Ve a https://console.cloud.google.com
2. Crea un proyecto o selecciona uno existente
3. Habilita "Google+ API" en APIs & Services
4. Crea credenciales OAuth 2.0 (Web application)
5. Agrega redirect URI: https://tu-app.onrender.com/api/auth/google/callback
6. Copia GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET a .env
"""

import os
from typing import Optional, Dict, Any
from urllib.parse import urlencode

import httpx

# Configuración desde variables de entorno
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")

# URLs de Google OAuth
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Scopes solicitados
SCOPES = ["openid", "email", "profile"]


def esta_configurado() -> bool:
    """Verifica si Google OAuth está configurado."""
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


def obtener_url_autenticacion(redirect_uri: Optional[str] = None) -> str:
    """
    Genera la URL de redirección a Google para autenticación.
    
    Args:
        redirect_uri: URI de callback (si no se proporciona, usa la configurada en .env)
    """
    if not esta_configurado():
        raise ValueError("Google OAuth no está configurado. Revisa GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET en .env")
    
    callback = redirect_uri or GOOGLE_REDIRECT_URI
    if not callback:
        raise ValueError("GOOGLE_REDIRECT_URI no está configurada en .env")
    
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": callback,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def intercambiar_codigo_por_token(code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
    """
    Intercambia el código de autorización por un access token.
    
    Args:
        code: Código de autorización de Google
        redirect_uri: Debe coincidir con el usado en obtener_url_autenticacion
    
    Returns:
        Dict con access_token, refresh_token, etc.
    """
    callback = redirect_uri or GOOGLE_REDIRECT_URI
    
    async with httpx.AsyncClient() as client:
        response = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": callback,
            "grant_type": "authorization_code",
        })
        
        if response.status_code != 200:
            raise Exception(f"Error obteniendo token de Google: {response.text}")
        
        return response.json()


async def obtener_info_usuario(access_token: str) -> Dict[str, Any]:
    """
    Obtiene la información del usuario desde Google.
    
    Args:
        access_token: Token de acceso de Google
    
    Returns:
        Dict con id, email, name, picture, etc.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code != 200:
            raise Exception(f"Error obteniendo info de usuario de Google: {response.text}")
        
        return response.json()


async def procesar_callback_google(code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
    """
    Flujo completo: código → token → info usuario.
    
    Args:
        code: Código de autorización de Google
        redirect_uri: URI de callback
    
    Returns:
        Dict con email, nombre, proveedor='google'
    """
    token_data = await intercambiar_codigo_por_token(code, redirect_uri)
    access_token = token_data.get("access_token")
    
    if not access_token:
        raise Exception("No se obtuvo access_token de Google")
    
    user_info = await obtener_info_usuario(access_token)
    
    return {
        "email": user_info.get("email", "").lower(),
        "nombre": user_info.get("name", "Usuario Google"),
        "proveedor": "google",
        "google_id": user_info.get("id"),
        "picture": user_info.get("picture"),
    }
