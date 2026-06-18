# Tipos de Enmascaramiento

Este proyecto implementa un motor dinámico de enmascaramiento en `masking.py` con las siguientes opciones:

## 1. Redacción (`redaccion`)
- Reemplaza cada carácter del valor original con `X`.
- Resultado: el texto conserva longitud, pero no es reversible.

## 2. Hashing (`hashing`)
- Aplica `SHA-256` al valor original.
- Devuelve los primeros 16 caracteres del hash seguidos de `...`.
- Resultado: no reversible y útil para proteger datos mientras mantiene consistencia de formato parcial.

## 3. Encriptación reversible (`encriptacion`)
- Usa `cryptography.Fernet` para cifrar el valor.
- El resultado es un token cifrado, pero la implementación lo muestra truncado como `enc::...`.
- Resultado: reversible si se tiene la clave Fernet almacenada en `.keyfile`.

## 4. FPE simulado (`fpe`)
- Simula un cifrado de preservación de formato mediante hashing iterativo SHA-256.
- Conserva la longitud del texto original al devolver la cantidad de caracteres igual al valor original.
- Resultado: no es un FPE estándar real, sino una aproximación con mayor carga de CPU.

## Nota importante
El algoritmo `fpe` se describe en el proyecto como "FPE simulado", por lo que no es una implementación formal de cifrado que preserva formato, sino una técnica basada en hash iterativo para mantener longitud.
