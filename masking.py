"""
masking.py — Motor de Enmascaramiento Dinámico
La clave Fernet se genera UNA vez y se persiste en .keyfile.
Si el servidor se reinicia, la clave se recupera del archivo y los backups SDM
siguen siendo descifrables.
"""
import hashlib
import os
import re
from cryptography.fernet import Fernet
from typing import List, Dict, Any, Optional

from config import settings

KEYFILE_PATH = os.path.join(settings.DATA_DIR, ".keyfile")

def _cargar_o_generar_clave() -> bytes:
    """
    Garantiza que la clave Fernet sea persistente.
    Prioridad: Variable de Entorno > Archivo Local.
    """
    # 1. Intentar cargar desde Variable de Entorno (Recomendado para Render/Producción)
    env_key = os.getenv("ENMASK_MASTER_KEY")
    if env_key:
        try:
            return env_key.encode("utf-8")
        except Exception:
            pass

    # 2. Intentar cargar desde archivo local
    if os.path.exists(KEYFILE_PATH):
        with open(KEYFILE_PATH, "rb") as f:
            clave = f.read().strip()
        print(f"[KEYFILE] Clave Fernet cargada desde '{KEYFILE_PATH}'.")
        return clave
    else:
        # 3. Generar nueva clave
        clave = Fernet.generate_key()
        with open(KEYFILE_PATH, "wb") as f:
            f.write(clave)
        try:
            os.chmod(KEYFILE_PATH, 0o600)
        except AttributeError:
            pass
        print(f"[KEYFILE] Nueva clave Fernet generada y guardada en '{KEYFILE_PATH}'.")
        return clave


# Clave global persistente — se carga una sola vez al importar el módulo
FERNET_KEY = _cargar_o_generar_clave()
cipher_suite = Fernet(FERNET_KEY)


def aplicar_enmascaramiento(datos: List[Dict[str, Any]], reglas: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Motor de reglas dinámicas. Recibe:
      - datos: Lista de diccionarios (filas de la BD)
      - reglas: {"nombre_columna": "algoritmo"} configurado por el usuario en la UI
    Retorna la misma lista con los valores sensibles transformados.
    """
    if not reglas:
        return datos

    datos_enmascarados = []
    for fila in datos:
        nueva_fila = fila.copy()
        for columna, algoritmo in reglas.items():
            if columna in nueva_fila and nueva_fila[columna] is not None:
                valor = str(nueva_fila[columna])

                # ── 1. REDACCIÓN DESTRUCTIVA ──────────────────────────────
                if algoritmo == "redaccion":
                    nueva_fila[columna] = "X" * len(valor)

                # ── 2. HASHING RÁPIDO (SHA-256) ───────────────────────────
                elif algoritmo == "hashing":
                    nueva_fila[columna] = (
                        hashlib.sha256(valor.encode("utf-8")).hexdigest()[:16] + "..."
                    )

                # ── 3. ENCRIPTACIÓN REVERSIBLE (FERNET / AES-128-CBC) ─────
                elif algoritmo == "encriptacion":
                    token = cipher_suite.encrypt(valor.encode("utf-8"))
                    nueva_fila[columna] = f"enc::{token.decode('utf-8')[:30]}..."

                # ── 4. FPE SIMULADO (ALTA CARGA DE CPU) ───────────────────
                elif algoritmo == "fpe":
                    hash_val = valor.encode("utf-8")
                    for _ in range(5000):
                        hash_val = hashlib.sha256(hash_val).digest()
                    nueva_fila[columna] = hash_val.hex()[: len(valor)]

        datos_enmascarados.append(nueva_fila)
    return datos_enmascarados


def cifrar_valor(texto: str) -> str:
    """Cifra un string con la clave Fernet persistente. Usado por SDM para backups."""
    return cipher_suite.encrypt(texto.encode("utf-8")).decode("utf-8")


def descifrar_valor(token: str) -> str:
    """Descifra un token Fernet. Usado por SDM durante la restauración."""
    return cipher_suite.decrypt(token.encode("utf-8")).decode("utf-8")


def mask_name(value: Optional[str]) -> str:
    if value is None:
        return ""
    partes = [p for p in re.split(r"(\s+)", str(value).strip()) if p != ""]
    resultado = []
    for parte in partes:
        if parte.isspace():
            resultado.append(parte)
        elif re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", parte):
            resultado.append(parte[:1] + ("*" * max(len(parte) - 1, 0)))
        else:
            resultado.append(parte)
    return "".join(resultado)


def mask_email(value: Optional[str]) -> str:
    if value is None:
        return ""
    texto = str(value).strip()
    if "@" not in texto:
        return mask_generic(texto)
    local, domain = texto.split("@", 1)
    if len(local) <= 3:
        local_mask = local[:1] + ("*" * max(len(local) - 1, 0))
    else:
        local_mask = local[:3] + ("*" * max(len(local) - 3, 0))
    return f"{local_mask}@{domain}"


def mask_phone(value: Optional[str]) -> str:
    if value is None:
        return ""
    digits = re.sub(r"\D", "", str(value))
    if len(digits) <= 5:
        return mask_generic(digits)
    head = digits[:3]
    tail = digits[-2:]
    middle = "*" * max(len(digits) - 5, 0)
    return f"{head}{middle}{tail}"


def mask_dni(value: Optional[str]) -> str:
    if value is None:
        return ""
    texto = re.sub(r"\s+", "", str(value).strip())
    if len(texto) <= 4:
        return mask_generic(texto)
    head = texto[:3]
    tail = texto[-1:]
    middle = "*" * max(len(texto) - 4, 0)
    return f"{head}{middle}{tail}"


def mask_generic(value: Optional[str]) -> str:
    if value is None:
        return ""
    texto = str(value)
    if len(texto) <= 2:
        return texto[:1] + ("*" * max(len(texto) - 1, 0))
    if len(texto) <= 5:
        return texto[:1] + ("*" * max(len(texto) - 2, 0)) + texto[-1:]
    return texto[:2] + ("*" * max(len(texto) - 4, 0)) + texto[-2:]


def academic_mask_value(value: Optional[str], mask_type: str = "generic") -> str:
    mask_type = (mask_type or "generic").strip().lower()
    if mask_type == "name":
        return mask_name(value)
    if mask_type == "email":
        return mask_email(value)
    if mask_type == "phone":
        return mask_phone(value)
    if mask_type == "dni":
        return mask_dni(value)
    return mask_generic(value)
