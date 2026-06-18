"""
oauth_google.py — Autenticación con Google OAuth2
"""

import os
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

# Configuración desde variables de entorno
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

# Configuración de OAuth
config = Config(environ={
    'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID,
    'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET,
})

oauth = OAuth(config)

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)


def get_google_auth_url(request):
    """Genera la URL de autorización de Google."""
    redirect_uri = GOOGLE_REDIRECT_URI
    return oauth.google.authorize_redirect(request, redirect_uri)


async def get_google_user_info(request):
    """Obtiene la información del usuario después de la autenticación."""
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')
    return user_info
