# UNIVERSIDAD PRIVADA DE TACNA

## FACULTAD DE INGENIERÍA

### Escuela Profesional de Ingeniería de Sistemas

---

# Proyecto SecOps — Enmask v2.0

## Curso: BASE DE DATOS II

### Docente:
Mag. Patrick Cuadros Quiroga

### Integrantes:
- Flores Navarro, Eduardo Gino (2023076793)
- Choqueña Mauricio Adrian (2023076799)

---

**Tacna – Perú**
**2026**

---

## CONTROL DE VERSIONES

| Versión | Hecha por | Revisada por | Aprobada por | Fecha | Motivo |
|---|---|---|---|---|---|
| 1.0 | EFN | MAC | — | Junio 2026 | Versión Original |

---

# FD03 — Informe de Especificación de Requerimientos

## Sistema Enmask v2.0

### Multi-DB Masking & Performance Overhead Monitor

---

## ÍNDICE GENERAL

| Nro | Sección | Pág |
|---|---|---|
| | **INTRODUCCIÓN** | 4 |
| **I** | **Generalidades de la Empresa** | 5 |
| | 1. Nombre de la Empresa | 5 |
| | 2. Visión | 5 |
| | 3. Misión | 5 |
| | 4. Organigrama | 5 |
| **II** | **Visionamiento de la Empresa** | 5 |
| | 1. Descripción del Problema | 5 |
| | 2. Objetivos de Negocios | 5 |
| | 3. Objetivos de Diseño | 5 |
| | 4. Alcance del proyecto | 5 |
| | 5. Viabilidad del Sistema | 5 |
| | 6. Información obtenida del Levantamiento de Información | 6 |
| **III** | **Análisis de Procesos** | 6 |
| | a) Diagrama del Proceso Actual – Diagrama de actividades | 6 |
| | b) Diagrama del Proceso Propuesto – Diagrama de actividades Inicial | 7 |
| **IV** | **Especificación de Requerimientos de Software** | 7 |
| | a) Cuadro de Requerimientos Funcionales Inicial | 7 |
| | b) Cuadro de Requerimientos No Funcionales | 7 |
| | c) Cuadro de Requerimientos Funcionales Final | 8 |
| | d) Reglas de Negocio | 9 |
| **V** | **Fase de Desarrollo** | 12 |
| | 1. Perfiles de Usuario | 12 |
| | 2. Modelo Conceptual | 12 |
| | a) Diagrama de Paquetes | 12 |
| | b) Diagrama de Casos de Uso | 13 |
| | c) Escenarios de Caso de Uso (narrativa) | 14 |
| | 3. Modelo Lógico | 23 |
| | a) Análisis de Objetos | 23 |
| | b) Diagrama de Actividades con objetos | 32 |
| | c) Diagrama de Secuencia | 37 |
| | d) Diagrama de Clases | 42 |
| | **CONCLUSIONES** | 46 |
| | **RECOMENDACIONES** | 46 |
| | **BIBLIOGRAFÍA** | 46 |
| | **WEBGRAFÍA** | 47 |

---

## INTRODUCCIÓN

El presente documento, identificado como **FD03 — Informe de Especificación de Requerimientos**, constituye la tercera entrega formal del proyecto **Enmask v2.0**, una plataforma de enmascaramiento y encriptación estática de datos diseñada para proteger información sensible (PII) en entornos no productivos.

El documento parte de los fundamentos establecidos en el FD01 (Informe de Factibilidad) y el FD02 (Documento de Visión), donde se definió la viabilidad técnica, económica y operativa del proyecto, así como el alcance, las capacidades y las restricciones del sistema. En este FD03, se procede a la especificación detallada de los requerimientos de software, incluyendo requerimientos funcionales, no funcionales, reglas de negocio, perfiles de usuario, diagramas UML (casos de uso, actividades, secuencia y clases) y el análisis de objetos del sistema.

El sistema Enmask v2.0 se distingue por su capacidad de operar sobre **7 motores de bases de datos** (PostgreSQL, MySQL, SQL Server, MongoDB, Cassandra, Redis y Neo4j), delegando el procesamiento de enmascaramiento a las funciones nativas de cada motor para garantizar un rendimiento óptimo. Adicionalmente, el sistema incorpora un **monitor de rendimiento e infraestructura** que permite cuantificar el "impuesto de rendimiento" (overhead) que la seguridad introduce en las consultas.

Este documento está dirigido al equipo de desarrollo, al docente del curso y a los futuros usuarios del sistema, y servirá como guía técnica para la implementación de las funcionalidades descritas.

---

## I. GENERALIDADES DE LA EMPRESA

### 1. Nombre de la Empresa

**Enmask v2.0** — Plataforma de Protección de Datos Sensibles y Monitoreo de Rendimiento.

El nombre "Enmask" proviene de la combinación de "Encrypt" (encriptar) y "Mask" (enmascarar), representando las dos funcionalidades centrales del sistema.

### 2. Visión

Ser una plataforma de referencia en protección de datos sensibles para entornos no productivos, reconocida por su capacidad de operar de manera unificada sobre múltiples motores de bases de datos, garantizando rendimiento, seguridad y cumplimiento normativo, contribuyendo a la cultura de seguridad de la información en las organizaciones y en el ámbito académico.

### 3. Misión

Desarrollar e implementar una plataforma web que permita a las organizaciones y profesionales de TI proteger información sensible (PII) mediante técnicas de enmascaramiento y encriptación estática, delegando el procesamiento a los motores nativos de bases de datos para garantizar un rendimiento superior, ofreciendo una interfaz unificada, trazabilidad completa mediante auditoría y gestión segura de llaves criptográficas.

### 4. Organigrama del Proyecto

```
                    ┌─────────────────────────┐
                    │   Director de Proyecto   │
                    │   (Eduardo Flores N.)    │
                    └───────────┬─────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
    ┌───────────▼───┐  ┌───────▼───────┐  ┌───▼───────────┐
    │  Backend Lead  │  │ Frontend Lead │  │  QA / DevOps  │
    │ (M. Choqueña)  │  │ (E. Flores)   │  │ (E. Flores)   │
    └───────────────┘  └───────────────┘  └───────────────┘
```

**Roles del equipo:**

| Rol | Responsable | Responsabilidades |
|---|---|---|
| Director de Proyecto | Eduardo Flores N. | Coordinación general, documentación, presentaciones |
| Backend Lead | Mauricio Choqueña | API REST, motor de enmascaramiento, integración con motores BD |
| Frontend Lead | Eduardo Flores N. | Interfaz de usuario, dashboard, experiencia de usuario |
| QA / DevOps | Eduardo Flores N. | Pruebas, contenerización Docker, despliegue |

---

## II. VISIONAMIENTO DE LA EMPRESA

### 1. Descripción del Problema

Las organizaciones manejan grandes volúmenes de datos sensibles (PII) que deben ser protegidos tanto en entornos productivos como en copias utilizadas para desarrollo, pruebas y análisis. Las soluciones tradicionales presentan las siguientes problemáticas:

1. **Procesamiento ineficiente:** El enmascaramiento en la capa de aplicación genera cuellos de botella al mover grandes volúmenes de datos por la red.

2. **Fragmentación de herramientas:** Cada motor de base de datos requiere scripts específicos, duplicando esfuerzos e introduciendo inconsistencias.

3. **Riesgos de seguridad:** La falta de un sistema centralizado de gestión de llaves y auditoría expone a las organizaciones a fugas de datos y sanciones regulatorias.

4. **Ausencia de métricas de rendimiento:** No existe visibilidad cuantitativa del overhead que la seguridad introduce en las operaciones de base de datos.

5. **Incumplimiento normativo:** Las prácticas actuales no satisfacen los requisitos de GDPR, PCI-DSS ni la Ley N° 29733 de Perú.

### 2. Objetivos de Negocios

| Nro | Objetivo | Descripción |
|---|---|---|
| ON-1 | Automatizar la protección de datos | Eliminar procesos manuales de ofuscación mediante un sistema automatizado |
| ON-2 | Unificar la gestión multi-motor | Ofrecer una sola interfaz para 7 motores de bases de datos |
| ON-3 | Garantizar cumplimiento normativo | Implementar medidas técnicas alineadas con GDPR y Ley N° 29733 |
| ON-4 | Medir el impacto de la seguridad | Cuantificar el overhead de rendimiento introducido por el enmascaramiento |
| ON-5 | Reducir costos operativos | Minimizar el tiempo de DBAs y desarrolladores en tareas de protección |

### 3. Objetivos de Diseño

| Nro | Objetivo | Descripción |
|---|---|---|
| OD-1 | Arquitectura modular | Implementar Clean Architecture con separación de capas (API, Servicios, Persistencia) |
| OD-2 | Patrón Factory para motores | Centralizar la creación de conexiones a BD en un DatabaseFactory |
| OD-3 | Medición precisa de tiempos | Utilizar `time.perf_counter_ns()` para capturar deltas de rendimiento |
| OD-4 | Microservicios desacoplados | Separar API Gateway, Masking Service y Monitor Service |
| OD-5 | Frontend reactivo | Dashboard con actualización automática cada 5 segundos |

### 4. Alcance del Proyecto

#### Incluido en el Proyecto (Funcionalidades Entregables)

| Área | Elementos Incluidos |
|---|---|
| **Motores de BD Soportados** | PostgreSQL, MySQL, SQL Server, SQLite, MongoDB, Redis, Neo4j |
| **Algoritmos de Enmascaramiento** | Redacción (X), Hashing (SHA-256), Encriptación (Fernet/AES), FPE simulado |
| **Gobernanza SDM** | Protección permanente (SDM), restauración de datos, backup cifrado |
| **Monitoreo de Rendimiento** | Delta de latencia, consumo de CPU, eficiencia de algoritmos |
| **Monitoreo de Infraestructura** | CPU, RAM, disco, uptime, salud de servicios y motores BD |
| **Seguridad** | Login bcrypt, Google OAuth2, cookies HTTP-only, gestión de claves Fernet |
| **Dashboard de Observabilidad** | Security Dashboard, Health Monitor, Database Observatory, Algorithm Analytics |
| **Despliegue** | Docker Compose, Render (nube), variables de entorno |

#### Excluido del Proyecto (Fuera de Alcance)

| Área | Elementos Excluidos |
|---|---|
| Enmascaramiento dinámico (proxy SQL) | No se implementa enmascaramiento en tiempo real |
| Motores adicionales | Oracle, DB2, Firebird, Couchbase, Elasticsearch |
| Anonimización estadística | k-anonimidad, l-diversidad, privacidad diferencial |
| Autenticación LDAP/Active Directory | Solo login local y Google OAuth2 |
| Alertas por correo/SMS | No se implementa sistema de notificaciones |
| CLI (interfaz de línea de comandos) | Solo interfaz web y API REST |
| Migración de esquemas | No se realizan cambios estructurales en las BD destino |

### 5. Viabilidad del Sistema

La viabilidad del sistema Enmask v2.0 fue evaluada en el FD01 (Informe de Factibilidad) en cinco dimensiones:

| Dimensión | Resultado | Justificación |
|---|---|---|
| **Técnica** | ✅ VIABLE | Todas las tecnologías son maduras, de código abierto y ampliamente adoptadas |
| **Económica** | ✅ VIABLE | Costos mínimos ($10 USD) gracias a herramientas gratuitas y créditos educativos |
| **Legal** | ✅ VIABLE | Cumple con GDPR Art. 32 y Ley N° 29733; licencias MIT/GPL sin restricciones |
| **Social** | ✅ VIABLE | Aceptación positiva por desarrolladores, DBAs y auditores |
| **Ambiental** | ✅ VIABLE | Reducción de almacenamiento y transferencia de datos vs. métodos tradicionales |

**Riesgo general del proyecto: MODERADO - CONTROLADO.** Todos los riesgos identificados (técnicos, de seguridad, operativos y de rendimiento) cuentan con estrategias de mitigación concretas.

### 6. Información Obtenida del Levantamiento de Información

El levantamiento de información se realizó mediante:

1. **Análisis de la situación actual:** Identificación de 7 brechas críticas (procesamiento, cobertura, integridad, seguridad, cumplimiento, rendimiento, auditoría).

2. **Benchmark de herramientas existentes:** Evaluación de soluciones comerciales y open-source de enmascaramiento.

3. **Consulta de documentación técnica:** Revisión de la documentación oficial de los 7 motores de BD soportados.

4. **Análisis normativo:** Estudio de GDPR, PCI-DSS, HIPAA y Ley N° 29733.

5. **Definición de requerimientos:** Extracción de 25 requerimientos funcionales y 20 no funcionales basados en las necesidades identificadas.

---

## III. ANÁLISIS DE PROCESOS

### a) Diagrama del Proceso Actual – Diagrama de actividades

El proceso actual de protección de datos en entornos no productivos sigue los siguientes pasos:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESO ACTUAL (Sin Enmask)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐                                                │
│  │ 1. Solicitud │                                                │
│  │   de copia   │                                                │
│  └──────┬───────┘                                                │
│         ▼                                                         │
│  ┌──────────────┐                                                │
│  │ 2. DBA genera│  pg_dump / mysqldump / mongodump              │
│  │   volcado    │  (consume recursos del servidor productivo)    │
│  └──────┬───────┘                                                │
│         ▼                                                         │
│  ┌──────────────┐                                                │
│  │ 3. Transferir│  Archivos grandes por red interna             │
│  │   a entorno  │  (sin cifrado, vulnerable a interceptación)   │
│  │   de destino │                                                │
│  └──────┬───────┘                                                │
│         ▼                                                         │
│  ┌──────────────┐                                                │
│  │ 4. Restaurar │  En entorno de desarrollo/pruebas             │
│  │   volcado    │                                                │
│  └──────┬───────┘                                                │
│         ▼                                                         │
│  ┌──────────────┐                                                │
│  │ 5. Scripts   │  Python/Bash/Java ad-hoc                      │
│  │   manuales   │  (frágiles, sin documentación, inconsistentes)│
│  │  de ofuscación│                                               │
│  └──────┬───────┘                                                │
│         ▼                                                         │
│  ┌──────────────┐                                                │
│  │ 6. Datos     │  Sin auditoría, sin trazabilidad              │
│  │   parcialmente│  Campos anidados omitidos                     │
│  │   protegidos │  Relaciones referencias rotas                  │
│  └──────────────┘                                                │
│                                                                   │
│  PROBLEMAS:                                                       │
│  • Proceso manual y lento (horas/días)                           │
│  • Scripts frágiles que se rompen con cambios de esquema         │
│  • Sin auditoría de accesos                                      │
│  • Riesgo de exposición de PII                                   │
│  • Incumplimiento normativo                                      │
└─────────────────────────────────────────────────────────────────┘
```

### b) Diagrama del Proceso Propuesto – Diagrama de actividades Inicial

```
┌─────────────────────────────────────────────────────────────────┐
│                 PROCESO PROPUESTO (Con Enmask v2.0)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐                                            │
│  │ 1. Usuario se    │  Email + Bcrypt o Google OAuth2            │
│  │   autentica      │  → Token de sesión HTTP-only               │
│  └──────┬───────────┘                                            │
│         ▼                                                         │
│  ┌──────────────────┐                                            │
│  │ 2. Configurar    │  Seleccionar motor + credenciales          │
│  │   conexión a BD  │  → DatabaseFactory instancia el conector   │
│  └──────┬───────────┘                                            │
│         ▼                                                         │
│  ┌──────────────────┐                                            │
│  │ 3. Definir       │  Seleccionar tabla, columna, algoritmo    │
│  │   reglas de      │  Redacción | Hashing | Encriptación | FPE │
│  │   enmascaramiento│                                            │
│  └──────┬───────────┘                                            │
│         ▼                                                         │
│  ┌──────────────────┐                                            │
│  │ 4. Ejecutar      │  API Gateway → Masking Service             │
│  │   benchmark      │  → Consulta cruda (mide tiempo_normal_ms)  │
│  │   comparativo    │  → Enmascaramiento (mide tiempo_mask_ms)   │
│  │                  │  → Cifrado (mide tiempo_encrypted_ms)      │
│  └──────┬───────────┘                                            │
│         ▼                                                         │
│  ┌──────────────────┐                                            │
│  │ 5. Almacenar     │  Monitor Service → SQLite                  │
│  │   métricas       │  (overhead_total_ms, filas_procesadas)     │
│  └──────┬───────────┘                                            │
│         ▼                                                         │
│  ┌──────────────────┐                                            │
│  │ 6. Visualizar    │  Dashboard con 4 módulos:                  │
│  │   resultados     │  • Security Dashboard                      │
│  │                  │  • Health Monitor                           │
│  │                  │  • Database Observatory                     │
│  │                  │  • Algorithm Analytics                      │
│  └──────────────────┘                                            │
│                                                                   │
│  BENEFICIOS:                                                      │
│  • Proceso automatizado (segundos/minutos)                       │
│  • Procesamiento nativo en el motor de BD                        │
│  • Auditoría completa de accesos                                 │
│  • Cumplimiento normativo                                        │
│  • Métricas cuantitativas de rendimiento                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## IV. ESPECIFICACIÓN DE REQUERIMIENTOS DE SOFTWARE

### a) Cuadro de Requerimientos Funcionales Inicial

Los requerimientos funcionales iniciales fueron definidos en base a la visión del proyecto (FD02) y la factibilidad técnica (FD01).

| ID | Requerimiento Funcional | Descripción | Prioridad |
|---|---|---|---|
| RF-I01 | Registro de usuario | El sistema permite crear cuenta con nombre, correo y contraseña | Alta |
| RF-I02 | Login con credenciales | Autenticación con email + bcrypt | Alta |
| RF-I03 | Login con Google OAuth2 | Autenticación mediante cuenta de Google | Media |
| RF-I04 | Conectar a motor de BD | Configurar conexión a cualquiera de los 7 motores soportados | Alta |
| RF-I05 | Obtener esquema de BD | Introspección automática de tablas y columnas | Alta |
| RF-I06 | Ejecutar test de enmascaramiento | Benchmark comparativo con medición de tiempos | Alta |
| RF-I07 | Aplicar redacción | Reemplazar caracteres por "X" | Alta |
| RF-I08 | Aplicar hashing SHA-256 | Generar hash irreversible del valor | Alta |
| RF-I09 | Aplicar encriptación Fernet | Cifrado simétrico AES-128-CBC reversible | Alta |
| RF-I10 | Aplicar FPE simulado | Cifrado que preserva formato mediante hash iterativo | Media |
| RF-I11 | Cifrar columna permanentemente | Encriptar valores de una columna con Fernet | Alta |
| RF-I12 | Descifrar columna | Restaurar valores originales de columna cifrada | Alta |
| RF-I13 | Activar gobernanza SDM | Protección permanente con backup cifrado | Alta |
| RF-I14 | Restaurar datos originales | Revertir protección SDM desde backup | Alta |
| RF-I15 | Consultar métricas de sistema | CPU, RAM, disco, uptime en tiempo real | Media |

### b) Cuadro de Requerimientos No Funcionales

| ID | Requerimiento No Funcional | Descripción | Métrica |
|---|---|---|---|
| RNF-01 | Tiempo de respuesta de consultas | Consultas a BD < 2s para 100 filas | p95 < 2000ms |
| RNF-02 | Overhead máximo de enmascaramiento | Masking no agrega > 5s al tiempo total | < 5000ms / 100 filas |
| RNF-03 | Rendimiento de cifrado/descifrado | Operaciones Fernet < 10s para 100 filas | < 10000ms |
| RNF-04 | Concurrencia | Soporte de 10 usuarios simultáneos | Respuesta < 5s |
| RNF-05 | Hashing seguro de contraseñas | Bcrypt con factor de trabajo adecuado | Rounds >= 12 |
| RNF-06 | Gestión de claves criptográficas | Clave Fernet persistente en .keyfile (permisos 0600) | Archivo protegido |
| RNF-07 | Cookies seguras | HttpOnly, SameSite=Lax, Secure en producción | Flags activos |
| RNF-08 | Manejo global de errores | Captura de excepciones sin exponer información interna | Error genérico al cliente |
| RNF-09 | Disponibilidad mínima | Uptime del 95% en horario de operación | 95% mensual |
| RNF-10 | Reinicio automático | Contenedores Docker con restart automático | `unless-stopped` |
| RNF-11 | Desacoplamiento de servicios | Comunicación HTTP REST entre microservicios | Endpoints independientes |
| RNF-12 | Extensibilidad de motores | Agregar motores implementando solo BaseDeDatos | Patrón Factory |
| RNF-13 | Separación de responsabilidades | Cada módulo con única responsabilidad | SRP |
| RNF-14 | Código documentado | Docstrings en español para funciones públicas | 100% funciones |
| RNF-15 | Configuración centralizada | Variables de entorno en config.py con .env | Archivo único |
| RNF-16 | Interfaz en español | UI, logs y documentación en español | Localización completa |
| RNF-17 | Diseño responsivo | Dashboard usable en pantallas >= 1024px | Tailwind CSS |
| RNF-18 | Actualización automática | Métricas se refrescan cada 5 segundos | Sin recarga |
| RNF-19 | Contenedorización Docker | Sistema completo en contenedores Docker | docker-compose.yml |
| RNF-20 | Despliegue en nube | Compatibilidad con Render Blueprint | render.yaml |

### c) Cuadro de Requerimientos Funcionales Final

Los requerimientos funcionales finales incorporan las validaciones realizadas durante el análisis de procesos y el levantamiento de información.

| ID | Requerimiento | Descripción | Prioridad | Endpoint |
|---|---|---|---|---|
| RF-001 | Registro de usuario | Crear cuenta con nombre, correo (único) y contraseña (min 8 chars) | Alta | `POST /api/auth/register` |
| RF-002 | Login local | Autenticación con email + bcrypt → cookie sesión | Alta | `POST /api/login` |
| RF-003 | Login Google OAuth2 | Autenticación vía Google → auto-registro si no existe | Media | `GET /auth/google/login` |
| RF-004 | Cierre de sesión | Revocar token + eliminar cookie | Alta | `POST /api/logout` |
| RF-005 | Usuario actual | Datos del usuario autenticado | Media | `GET /api/auth/me` |
| RF-006 | Conectar a BD | Configurar conexión (motor + credenciales + alias) → introspección esquema | Alta | `POST /api/v1/connect` |
| RF-007 | Listar conexiones | Conexiones activas del usuario (ID, alias, motor) | Media | `GET /api/v1/connections` |
| RF-008 | Eliminar conexión | Remover conexión de la sesión | Baja | `DELETE /api/v1/connections/{id}` |
| RF-009 | Obtener esquema | Estructura de tablas y columnas de la BD conectada | Alta | `GET /api/v1/schema` |
| RF-010 | Ejecutar benchmark | Test comparativo: consulta cruda + masking + cifrado con medición de tiempos | Alta | `POST /api/v1/execute_test` |
| RF-011 | Vista previa masking | Preview de enmascaramiento académico sin modificar BD | Media | `GET /mask/preview` |
| RF-012 | Vista académica | Tabla completa con datos enmascarados visualmente | Media | `GET /mask/view` |
| RF-013 | Encriptar columna | Cifrado permanente con Fernet (AES-128-CBC) | Alta | `POST /encrypt` |
| RF-014 | Desencriptar columna | Descifrado con clave Fernet | Alta | `POST /decrypt` |
| RF-015 | Activar SDM | Enmascaramiento estático con backup cifrado | Alta | `POST /api/v1/governance/protect` |
| RF-016 | Restaurar SDM | Revertir protección desde backup cifrado | Alta | `POST /api/v1/governance/restore` |
| RF-017 | Estado gobernanza | Verificar protección de tabla (ACTIVA/INACTIVA) | Media | `GET /api/v1/governance/status` |
| RF-018 | Métricas de sistema | CPU, RAM, disco, uptime en tiempo real | Alta | `GET /api/v1/monitor/system` |
| RF-019 | Salud de servicios | Estado (UP/DOWN) y latencia de los 3 microservicios | Alta | `GET /api/v1/monitor/services` |
| RF-020 | Salud de BD | Conectividad y estado de motores conectados | Alta | `GET /api/v1/monitor/databases` |
| RF-021 | Ranking algoritmos | Comparativa histórica de rendimiento por algoritmo | Media | `GET /api/v1/monitor/algorithms` |
| RF-022 | Estadísticas por motor | Métricas agrupadas por motor de BD | Media | `GET /api/v1/monitor/engine-stats` |
| RF-023 | Historial métricas | Registro completo de métricas de overhead | Media | `GET /api/v1/monitor/metrics` |
| RF-024 | Log de errores | Historial de errores operativos | Baja | `GET /api/v1/monitor/errors` |
| RF-025 | Health check global | Verificación de salud de los 3 microservicios | Alta | `GET /health` |

### d) Reglas de Negocio

Las reglas de negocio definen las restricciones y validaciones que el sistema debe aplicar en cada operación.

#### RN-001: Validación de Credenciales de Registro

| Campo | Valor |
|---|---|
| **ID** | RN-001 |
| **Descripción** | El correo electrónico debe ser único en el sistema. La contraseña debe tener al menos 8 caracteres. |
| **Validación** | `correo` no duplicado en tabla `users`; `len(password) >= 8` |
| **Excepción** | HTTP 409 (correo duplicado), HTTP 400 (contraseña < 8 chars) |

#### RN-002: Autenticación Requerida

| Campo | Valor |
|---|---|
| **ID** | RN-002 |
| **Descripción** | Todos los endpoints de la API (excepto `/health`, `/login`, `/api/auth/register`, `/auth/google/*`) requieren autenticación mediante cookie de sesión válida. |
| **Validación** | Cookie `session_token` presente y no revocada |
| **Excepción** | HTTP 302 redirect a `/login` (vista HTML) o HTTP 401 (API) |

#### RN-003: Motores de BD Soportados

| Campo | Valor |
|---|---|
| **ID** | RN-003 |
| **Descripción** | Solo se aceptan conexiones a los motores: postgres, mysql, sqlserver, sqlite, mongodb, redis, neo4j, mariadb, cassandra. |
| **Validación** | `motor.lower() in ["postgres", "mysql", "sqlserver", "sqlite", "mongodb", "redis", "neo4j", "mariadb", "cassandra"]` |
| **Excepción** | HTTP 400 "Motor no soportado" |

#### RN-004: Algoritmos de Enmascaramiento Válidos

| Campo | Valor |
|---|---|
| **ID** | RN-004 |
| **Descripción** | Los algoritmos de enmascaramiento aceptados son: `redaccion`, `hashing`, `encriptacion`, `fpe`. |
| **Validación** | `algoritmo in ["redaccion", "hashing", "encriptacion", "fpe"]` |
| **Excepción** | Algoritmo no reconocido → se omite la transformación |

#### RN-005: Medición de Tiempos

| Campo | Valor |
|---|---|
| **ID** | RN-005 |
| **Descripción** | Todas las mediciones de rendimiento deben usar `time.perf_counter_ns()` para garantizar precisión a nivel de nanosegundos. Los resultados se expresan en milisegundos (ms) con 3 decimales. |
| **Fórmula** | `overhead_total_ms = tiempo_normal_ms + tiempo_mask_ms + tiempo_encrypted_ms` |

#### RN-006: Gobernanza SDM — Motores Permitidos

| Campo | Valor |
|---|---|
| **ID** | RN-006 |
| **Descripción** | La gobernanza SDM (protección/restauración permanente) solo está disponible para: sqlite, postgres, sqlserver, mongodb, mysql, mariadb. |
| **Validación** | `motor_nombre in MOTORES_SDM_DISPONIBLES` |
| **Excepción** | HTTP 400 "SDM no disponible para [motor]" |

#### RN-007: Backup Cifrado Obligatorio

| Campo | Valor |
|---|---|
| **ID** | RN-007 |
| **Descripción** | Antes de aplicar SDM (Nivel 2), el sistema DEBE crear un backup cifrado de los valores originales usando Fernet. El backup se almacena en la tabla `_enmask_backup_[tabla]_[columna]`. |
| **Validación** | Backup creado exitosamente antes de sobrescribir datos |

#### RN-008: Clave Fernet Persistente

| Campo | Valor |
|---|---|
| **ID** | RN-008 |
| **Descripción** | La clave Fernet debe persistirse en el archivo `.keyfile` con permisos 0600. Si el archivo no existe, se genera una nueva clave. Si existe, se carga del archivo. La variable de entorno `ENMASK_MASTER_KEY` tiene prioridad sobre el archivo. |
| **Prioridad** | `ENMASK_MASTER_KEY` > `.keyfile` > Generar nueva |

#### RN-009: Unicidad de Conexiones por Sesión

| Campo | Valor |
|---|---|
| **ID** | RN-009 |
| **Descripción** | Cada conexión se almacena con un ID único (UUID) en la sesión del usuario. Un usuario puede tener múltiples conexiones activas simultáneamente. |
| **Validación** | `connection_id = uuid4()` |

#### RN-010: Límite de Consultas

| Campo | Valor |
|---|---|
| **ID** | RN-010 |
| **Descripción** | Las consultas de benchmark están limitadas a 100 filas por defecto (`limit=100`). Para gobernanza SDM, el límite es 1000 filas por lote. |
| **Validación** | `LIMIT 100` (benchmark), `LIMIT 1000` (SDM) |

#### RN-011: Excepciones Registradas

| Campo | Valor |
|---|---|
| **ID** | RN-011 |
| **Descripción** | Todas las excepciones no controladas deben registrarse en el Monitor Service mediante `POST /errors` con el formato: `{service, error_type, message, timestamp}`. |
| **Validación** | Global exception handler en `main.py` |

#### RN-012: Seguridad de Cookies

| Campo | Valor |
|---|---|
| **ID** | RN-012 |
| **Descripción** | Las cookies de sesión deben usar: `httponly=True`, `samesite="lax"`, `secure=True` (solo en producción/Render). |
| **Validación** | `_COOKIE_SECURE = os.getenv("RENDER") == "true"` |

#### RN-013: Formato de Respuesta de Benchmark

| Campo | Valor |
|---|---|
| **ID** | RN-013 |
| **Descripción** | El endpoint `/api/v1/execute_test` debe retornar exactamente: `{motor_utilizado, masking_mode, tiempo_normal_ms, tiempo_masked_ms, tiempo_encrypted_ms, latency_delta_ms, cpu_overhead, tiempo_bd_ms, tiempo_enmascarado_ms, overhead_total_ms, filas_procesadas, data}`. |

#### RN-014: Comunicación entre Microservicios

| Campo | Valor |
|---|---|
| **ID** | RN-014 |
| **Descripción** | La comunicación entre API Gateway ↔ Masking Service y API Gateway ↔ Monitor Service se realiza exclusivamente vía HTTP (httpx). Los timeouts son: 10s (consultas), 30s (op. pesadas), 2s (métricas). |

#### RN-015: Introspección de Esquema

| Campo | Valor |
|---|---|
| **ID** | RN-015 |
| **Descripción** | Al conectar a una BD, el sistema DEBE obtener automáticamente el esquema (tablas/columnas) usando consultas nativas de cada motor: `information_schema` (SQL), `list_collection_names` (MongoDB), `keys("*")` (Redis), `MATCH (n)` (Neo4j). |

---

## V. FASE DE DESARROLLO

### 1. Perfiles de Usuario

#### Usuario Estándar (Rol User)

| Atributo | Descripción |
|---|---|
| **Perfil** | Desarrollador, DBA o analista de datos |
| **Competencias** | Conocimientos básicos de bases de datos, comprensión de la necesidad de proteger datos sensibles |
| **Objetivos** | Configurar conexiones, definir reglas de enmascaramiento, ejecutar benchmarks, visualizar métricas |
| **Permisos** | Crear/editar/eliminar sus propias conexiones, ejecutar tests, consultar sus métricas |

#### Administrador (Rol Admin)

| Atributo | Descripción |
|---|---|
| **Perfil** | Líder técnico, DBA senior o responsable de seguridad |
| **Competencias** | Conocimiento avanzado de seguridad de datos, administración de sistemas, normativas de protección |
| **Objetivos** | Supervisar el uso del sistema, gestionar auditorías, operaciones críticas (SDM, rotación de llaves) |
| **Permisos** | Todos los permisos de User + ver auditorías globales, gestionar gobernanza SDM, acceder a logs de errores |

### 2. Modelo Conceptual

#### a) Diagrama de Paquetes

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Enmask v2.0 — Arquitectura de Paquetes           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    <<capa presentación>>                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │    │
│  │  │  login.html   │  │  index.html   │  │  static/*        │  │    │
│  │  │  (Auth UI)    │  │  (Dashboard)  │  │  (CSS/JS)        │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                        │
│                              ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    <<capa API gateway>>                       │    │
│  │  ┌──────────────────────────────────────────────────────┐   │    │
│  │  │                    main.py                             │   │    │
│  │  │  • Autenticación (register, login, logout, OAuth2)    │   │    │
│  │  │  • Conexiones a BD (connect, list, delete, schema)    │   │    │
│  │  │  • Benchmark (execute_test)                           │   │    │
│  │  │  • Gobernanza (protect, restore, status)              │   │    │
│  │  │  • Monitoreo (system, services, databases, metrics)   │   │    │
│  │  └──────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│            │                    │                    │                 │
│            ▼                    ▼                    ▼                 │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│  │ <<capa auth>> │  │<<capa masking>>  │  │<<capa monitor>>  │       │
│  │              │  │                  │  │                  │       │
│  │ auth.py      │  │ masking_         │  │ monitor_         │       │
│  │ db_usuarios.py│  │   service.py    │  │   service.py     │       │
│  │ oauth_google.py│ │ masking.py      │  │ monitor.py       │       │
│  │              │  │ encryption_     │  │ health_monitor.py │       │
│  │              │  │   service.py    │  │ system_metrics.py │       │
│  │              │  │ key_manager.py  │  │ service_checker.py│       │
│  │              │  │ governance.py   │  │                  │       │
│  └──────────────┘  └──────────────────┘  └──────────────────┘       │
│            │                    │                    │                 │
│            ▼                    ▼                    ▼                 │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    <<capa datos>>                             │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │    │
│  │  │ database_     │  │  config.py    │  │  SQLite (monitor │  │    │
│  │  │   manager.py  │  │  (.env)       │  │  _metrics.db)    │  │    │
│  │  │ (Factory)     │  │              │  │                  │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                        │
│                              ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              <<motores de bases de datos>>                    │    │
│  │  ┌─────────┐ ┌───────┐ ┌──────────┐ ┌─────────┐ ┌───────┐ │    │
│  │  │PostgreSQL│ │ MySQL │ │SQL Server│ │ MongoDB │ │ Redis │ │    │
│  │  └─────────┘ └───────┘ └──────────┘ └─────────┘ └───────┘ │    │
│  │  ┌─────────┐ ┌───────┐                                      │    │
│  │  │  SQLite │ │ Neo4j │                                      │    │
│  │  └─────────┘ └───────┘                                      │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

#### b) Diagrama de Casos de Uso

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Diagrama de Casos de Uso — Enmask v2.0            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│                        ┌─────────────────┐                           │
│                        │   Enmask v2.0    │                           │
│                        │                  │                           │
│   ┌──────┐            │  ┌─────────────┐ │            ┌──────┐      │
│   │      │────────────┼──│ CU-001:     │ │            │      │      │
│   │User  │            │  │ Registrarse  │ │            │Google│      │
│   │      │────────────┼──│ CU-002:     │─┼────────────│OAuth │      │
│   │      │            │  │ Login        │ │            │      │      │
│   └──┬───┘            │  └─────────────┘ │            └──────┘      │
│      │                │                  │                           │
│      │                │  ┌─────────────┐ │                           │
│      │                │  │ CU-003:     │ │                           │
│      └────────────────┼──│ Conectar BD │ │                           │
│                       │  └─────────────┘ │                           │
│   ┌──────┐            │                  │                           │
│   │      │            │  ┌─────────────┐ │                           │
│   │      │────────────┼──│ CU-004:     │ │                           │
│   │      │            │  │ Ejecutar    │ │                           │
│   │ User │            │  │ Benchmark   │ │                           │
│   │      │            │  └─────────────┘ │                           │
│   │      │            │                  │                           │
│   │      │            │  ┌─────────────┐ │                           │
│   │      │────────────┼──│ CU-005:     │ │                           │
│   │      │            │  │ Cifrar /    │ │                           │
│   │      │            │  │ Descifrar   │ │                           │
│   │      │            │  └─────────────┘ │                           │
│   │      │            │                  │                           │
│   │      │            │  ┌─────────────┐ │                           │
│   │      │────────────┼──│ CU-006:     │ │                           │
│   │      │            │  │ Activar SDM │ │                           │
│   └──┬───┘            │  └─────────────┘ │                           │
│      │                │                  │                           │
│      │   ┌──────┐     │  ┌─────────────┐ │                           │
│      │   │      │     │  │ CU-007:     │ │                           │
│      └───│Admin │─────┼──│ Monitorear  │ │                           │
│          │      │     │  │ Sistema     │ │                           │
│          │      │     │  └─────────────┘ │                           │
│          │      │     │                  │                           │
│          │      │     │  ┌─────────────┐ │                           │
│          │      │─────┼──│ CU-008:     │ │                           │
│          │      │     │  │ Restaurar   │ │                           │
│          └──────┘     │  │ SDM         │ │                           │
│                       │  └─────────────┘ │                           │
│                       └─────────────────┘                           │
└─────────────────────────────────────────────────────────────────────┘
```

#### c) Escenarios de Caso de Uso (narrativa)

---

**CU-001: Registrarse en el Sistema**

| Campo | Descripción |
|---|---|
| **ID** | CU-001 |
| **Nombre** | Registro de nuevo usuario |
| **Actor** | Persona sin cuenta en el sistema |
| **Precondición** | El usuario tiene acceso a la URL del sistema |
| **Postcondición** | Cuenta creada, sesión activa |

**Flujo Principal:**
1. El usuario accede a `/login` en el navegador.
2. El sistema muestra el formulario de login.
3. El usuario hace clic en "Regístrate aquí".
4. El usuario ingresa su nombre, correo electrónico y contraseña (mínimo 8 caracteres).
5. El sistema valida que el correo no esté registrado.
6. El sistema genera un hash bcrypt de la contraseña.
7. El sistema almacena el usuario en la tabla `users` de SQLite.
8. El sistema crea un token de sesión y lo almacena en una cookie HTTP-only.
9. El sistema redirige al dashboard principal.

**Flujos Alternativos:**
- **5a.** Si el correo ya existe → El sistema retorna error 409 "Correo ya registrado". El usuario debe usar otro correo.
- **4a.** Si la contraseña tiene menos de 8 caracteres → El sistema retorna error 400 "La contraseña debe tener al menos 8 caracteres".

---

**CU-002: Iniciar Sesión**

| Campo | Descripción |
|---|---|
| **ID** | CU-002 |
| **Nombre** | Autenticación del usuario |
| **Actor** | Usuario registrado |
| **Precondición** | El usuario tiene una cuenta creada |
| **Postcondición** | Sesión activa, acceso al dashboard |

**Flujo Principal:**
1. El usuario accede a `/login`.
2. Ingresa su correo electrónico y contraseña.
3. El sistema busca el usuario por correo en la tabla `users`.
4. El sistema verifica la contraseña con bcrypt.
5. El sistema crea un token de sesión (`crear_token_sesion`).
6. El sistema establece la cookie `session_token` (httponly, samesite=lax).
7. El sistema retorna "Login exitoso" con el nombre del usuario.
8. El usuario es redirigido al dashboard `/`.

**Flujos Alternativos:**
- **3a.** Si el correo no existe → Error 401 "Correo o contraseña incorrectos".
- **4a.** Si la contraseña no coincide → Error 401 "Correo o contraseña incorrectos".

**Flujo con Google OAuth2:**
1. El usuario hace clic en "Continuar con Google".
2. El sistema redirige a `accounts.google.com`.
3. El usuario autoriza la aplicación.
4. Google redirige a `/auth/google/callback` con el código.
5. El sistema obtiene el userinfo (nombre, correo).
6. Si el usuario no existe, se registra automáticamente.
7. El sistema crea la sesión y redirige al dashboard.

---

**CU-003: Conectar a una Base de Datos**

| Campo | Descripción |
|---|---|
| **ID** | CU-003 |
| **Nombre** | Configurar conexión a motor de BD |
| **Actor** | Usuario autenticado |
| **Precondición** | Sesión activa, credenciales de BD disponibles |
| **Postcondición** | Conexión activa con esquema obtenido |

**Flujo Principal:**
1. El usuario selecciona el motor de BD (postgres, mysql, sqlserver, sqlite, mongodb, redis, neo4j).
2. El usuario ingresa las credenciales: host, puerto, usuario, contraseña, database.
3. El usuario opcionalmente ingresa un alias descriptivo.
4. El sistema instancia el motor correspondiente via `DatabaseFactory.obtener_motor()`.
5. El sistema prueba la conexión ejecutando `conectar()`.
6. El sistema obtiene el esquema ejecutando `obtener_esquema()`:
   - **SQL:** `SELECT table_name, column_name FROM information_schema.columns`
   - **MongoDB:** `list_collection_names()` + muestreo de documentos
   - **Redis:** `keys("*")` + inspección de tipos
   - **Neo4j:** `MATCH (n) RETURN labels(n), keys(n)`
7. El sistema almacena la conexión en la sesión del usuario con un UUID.
8. El sistema retorna `{connection_id, alias, esquema}`.

**Flujos Alternativos:**
- **4a.** Si el motor no es soportado → Error 400 "Motor no soportado".
- **5a.** Si las credenciales son incorrectas → Error 400 "Error conectando a BD".

---

**CU-004: Ejecutar Benchmark de Enmascaramiento**

| Campo | Descripción |
|---|---|
| **ID** | CU-004 |
| **Nombre** | Test comparativo de rendimiento con enmascaramiento |
| **Actor** | Usuario autenticado |
| **Precondición** | Conexión a BD activa, tabla seleccionada |
| **Postcondición** | Métricas almacenadas, datos enmascarados mostrados |

**Flujo Principal:**
1. El usuario selecciona una tabla de la conexión activa.
2. El usuario define reglas de enmascaramiento: `{columna: algoritmo}` (redaccion, hashing, encriptacion, fpe).
3. El usuario ejecuta el test.
4. La API Gateway envía la solicitud al Masking Service (`POST /benchmark`).
5. El Masking Service:
   - a. Ejecuta la consulta cruda a la BD → mide `tiempo_normal_ms` con `time.perf_counter_ns()`.
   - b. Aplica enmascaramiento según las reglas → mide `tiempo_mask_ms`.
   - c. Aplica cifrado Fernet → mide `tiempo_encrypted_ms`.
   - d. Calcula `latency_delta_ms` y `cpu_overhead`.
   - e. Retorna datos enmascarados + métricas.
6. La API Gateway calcula `overhead_total_ms = normal + mask + encrypted`.
7. La API Gateway envía las métricas al Monitor Service (`POST /metrics`).
8. El Monitor Service almacena en SQLite (`metrics`).
9. La API Gateway retorna al frontend: datos enmascarados + todas las métricas.
10. El frontend muestra la tabla comparativa y las métricas de rendimiento.

**Flujos Alternativos:**
- **5a.** Si la tabla no existe → Error desde el motor de BD.
- **5b.** Si la conexión se pierde → Error 500 con detalle.

---

**CU-005: Cifrar y Descifrar Datos**

| Campo | Descripción |
|---|---|
| **ID** | CU-005 |
| **Nombre** | Encriptar/Desencriptar columna con Fernet |
| **Actor** | Usuario autenticado |
| **Precondición** | Conexión a BD activa |
| **Postcondición** | Datos cifrados o descifrados permanentemente |

**Flujo Principal (Cifrado):**
1. El usuario selecciona tabla y columna.
2. El usuario presiona "Encriptar Datos".
3. La API envía solicitud al Masking Service (`POST /encrypt`).
4. El Masking Service lee los valores originales de la columna.
5. Para cada valor, aplica `cipher_suite.encrypt(valor.encode())`.
6. Escribe los tokens cifrados en la BD.
7. Retorna la cantidad de registros cifrados.

**Flujo Principal (Descifrado):**
1. El usuario selecciona tabla y columna cifrada.
2. El usuario presiona "Desencriptar Datos".
3. La API envía solicitud al Masking Service (`POST /decrypt`).
4. El Masking Service lee los tokens cifrados.
5. Para cada token, aplica `cipher_suite.decrypt(token.encode())`.
6. Escribe los valores originales en la BD.
7. Retorna la cantidad de registros descifrados.

**Flujos Alternativos:**
- **5a.** Si la clave Fernet no coincide → Error de descifrado (Fernet exception).

---

**CU-006: Activar Gobernanza SDM**

| Campo | Descripción |
|---|---|
| **ID** | CU-006 |
| **Nombre** | Proteger tabla con Static Data Masking |
| **Actor** | Administrador del sistema |
| **Precondición** | Conexión a BD activa, motor soportado para SDM |
| **Postcondición** | Tabla protegida, backup cifrado almacenado |

**Flujo Principal:**
1. El administrador selecciona tabla y define reglas de protección.
2. El administrador activa SDM.
3. La API verifica que el motor esté en `MOTORES_SDM_DISPONIBLES`.
4. La API envía solicitud al Masking Service (`POST /protect`).
5. El Masking Service:
   - a. Crea la tabla de backup `_enmask_backup_[tabla]_[columna]`.
   - b. Cifra los valores originales con Fernet y los almacena en el backup.
   - c. Aplica el enmascaramiento permanente a la tabla original.
   - d. Registra el estado de protección.
6. El sistema retorna `{estado: "ACTIVA", mensaje: "SDM activado en [tabla]"}`.

**Flujos Alternativos:**
- **3a.** Si el motor no está soportado → Error 400 "SDM no disponible para [motor]".
- **5a.** Si SDM ya está activo → Error 409 "Conflicto en pre-flight".

---

**CU-007: Monitorear el Sistema**

| Campo | Descripción |
|---|---|
| **ID** | CU-007 |
| **Nombre** | Observar estado del sistema e infraestructura |
| **Actor** | Usuario o Administrador |
| **Precondición** | Sistema en funcionamiento |
| **Postcondición** | Visibilidad completa del estado |

**Flujo Principal:**
1. El usuario accede al Health Monitor Dashboard.
2. El frontend realiza peticiones cada 5 segundos:
   - `GET /api/v1/monitor/system` → métricas de CPU, RAM, disco, uptime.
   - `GET /api/v1/monitor/services` → estado de los 3 microservicios.
   - `GET /api/v1/monitor/databases` → salud de motores conectados.
   - `GET /api/v1/monitor/algorithms` → ranking de algoritmos.
   - `GET /api/v1/monitor/engine-stats` → estadísticas por motor.
3. El Monitor Service consulta `psutil` para métricas de sistema.
4. El Monitor Service ejecuta health checks HTTP a los servicios.
5. El Monitor Service verifica conectividad a las BD configuradas.
6. El frontend muestra:
   - Gráficos temporales de CPU, RAM, disco (Chart.js).
   - Tabla de estado de servicios (UP/DOWN con indicadores verde/rojo).
   - Ranking de algoritmos por tiempo promedio.
   - Panel de alertas (CPU > 80%, RAM > 85%, Disco > 90%).

**Flujos Alternativos:**
- **2a.** Si un servicio está DOWN → Se muestra indicador rojo + alerta.
- **2b.** Si una BD no responde → Se muestra estado "DOWN" con latencia N/A.

---

**CU-008: Restaurar Datos Originales (Revertir SDM)**

| Campo | Descripción |
|---|---|
| **ID** | CU-008 |
| **Nombre** | Revertir protección SDM |
| **Actor** | Administrador del sistema |
| **Precondición** | SDM activo en la tabla (estado "ACTIVA") |
| **Postcondición** | Datos originales restaurados, protección removida |

**Flujo Principal:**
1. El administrador selecciona la tabla protegida.
2. El administrador confirma la restauración.
3. La API envía solicitud al Masking Service (`POST /restore`).
4. El Masking Service:
   - a. Lee los valores originales de la tabla de backup `_enmask_backup_[tabla]_[columna]`.
   - b. Descifra los valores usando `cipher_suite.decrypt()`.
   - c. Escribe los valores originales en la tabla principal.
   - d. Actualiza el estado de protección a "INACTIVA".
5. El sistema retorna `{estado: "INACTIVA", mensaje: "Datos restaurados en [tabla]"}`.

**Flujos Alternativos:**
- **4a.** Si la tabla de backup no existe → Error de restauración.
- **4b.** Si la clave Fernet no puede descifrar → Error de descifrado.

---

### 3. Modelo Lógico

#### a) Análisis de Objetos

El análisis de objetos describe las clases principales del sistema, sus atributos, métodos y responsabilidades.

---

**Clase: `BaseDeDatos` (Abstracta)**

| Aspecto | Descripción |
|---|---|
| **Ubicación** | `database_manager.py:18` |
| **Responsabilidad** | Definir el contrato común para todos los motores de bases de datos |
| **Patrón** | Template Method / Strategy |

**Atributos:**
| Atributo | Tipo | Descripción |
|---|---|---|
| `credenciales` | `Dict[str, Any]` | Diccionario con host, puerto, usuario, contraseña, database |

**Métodos:**
| Método | Retorno | Descripción |
|---|---|---|
| `conectar()` | `Connection` | Establece conexión al motor de BD |
| `obtener_esquema()` | `Dict[str, List[str]]` | Retorna `{tablas: {nombre: [columnas]}}` |
| `ejecutar_consulta(query, **kwargs)` | `List[Dict[str, Any]]` | Ejecuta consulta y retorna filas como diccionarios |

**Subclases implementadas:**
- `PostgresDB` → psycopg2 + RealDictCursor
- `MySQLDB` → pymysql + DictCursor
- `SQLiteDB` → sqlite3 + Row factory
- `SQLServerDB` → pymssql + as_dict=True
- `MongoDB` → pymongo + MongoClient
- `RedisDB` → redis-py + decode_responses
- `Neo4jDB` → neo4j + GraphDatabase.driver
- `CassandraDB` → cassandra-driver

---

**Clase: `DatabaseFactory`**

| Aspecto | Descripción |
|---|---|
| **Ubicación** | `database_manager.py:346` |
| **Responsabilidad** | Instanciar el motor de BD correcto según el nombre proporcionado |
| **Patrón** | Factory Method |

**Métodos:**
| Método | Retorno | Descripción |
|---|---|---|
| `obtener_motor(motor, credenciales)` | `BaseDeDatos` | Retorna la instancia del motor correspondiente |

**Mapeo de motores:**
```python
motores = {
    "postgres": PostgresDB,
    "mysql": MySQLDB,
    "sqlserver": SQLServerDB,
    "sqlite": SQLiteDB,
    "mongodb": MongoDB,
    "redis": RedisDB,
    "neo4j": Neo4jDB,
    "mariadb": MySQLDB,
    "cassandra": CassandraDB
}
```

---

**Clase: `Settings` (Configuración)**

| Aspecto | Descripción |
|---|---|
| **Ubicación** | `config.py:11` |
| **Responsabilidad** | Centralizar toda la configuración del sistema desde variables de entorno |
| **Patrón** | Singleton (instancia global `settings`) |

**Atributos principales:**
| Atributo | Tipo | Default | Descripción |
|---|---|---|---|
| `APP_NAME` | str | "Multi-DB Masking..." | Nombre de la aplicación |
| `DEBUG` | bool | True | Modo debug |
| `DATA_DIR` | str | "." | Directorio de datos persistentes |
| `PG_HOST` | str | "localhost" | Host de PostgreSQL |
| `PG_PORT` | int | 5432 | Puerto de PostgreSQL |
| `MYSQL_HOST` | str | "localhost" | Host de MySQL |
| `MONGO_URI` | str | "mongodb://..." | URI de MongoDB |
| `REDIS_HOST` | str | "localhost" | Host de Redis |
| `NEO4J_URI` | str | "bolt://..." | URI de Neo4j |

---

**Clase: `Masking Engine` (Motor de Enmascaramiento)**

| Aspecto | Descripción |
|---|---|
| **Ubicación** | `masking.py` |
| **Responsabilidad** | Aplicar algoritmos de enmascaramiento a los datos |

**Funciones principales:**
| Función | Descripción |
|---|---|
| `aplicar_enmascaramiento(datos, reglas)` | Motor de reglas dinámicas: aplica algoritmos según reglas `{columna: algoritmo}` |
| `cifrar_valor(texto)` | Cifra un string con Fernet (usado por SDM para backups) |
| `descifrar_valor(token)` | Descifra un token Fernet (usado en restauración SDM) |
| `mask_name(value)` | Enmascara nombre: "Eduardo" → "E******" |
| `mask_email(value)` | Enmascara email: "test@mail.com" → "tes*@mail.com" |
| `mask_phone(value)` | Enmascara teléfono: "987654321" → "987***321" |
| `mask_dni(value)` | Enmascara DNI: "12345678" → "123****8" |
| `mask_generic(value)` | Enmascara genérico: "abcdefgh" → "ab****gh" |
| `academic_mask_value(value, tipo)` | Enrutador de máscaras académicas por tipo |

**Algoritmos de enmascaramiento:**
| Algoritmo | Implementación | Reversible |
|---|---|---|
| `redaccion` | `"X" * len(valor)` | No |
| `hashing` | `SHA-256(valor)[:16] + "..."` | No |
| `encriptacion` | `Fernet(valor)[:30] + "..."` | Sí (con clave) |
| `fpe` | Hash iterativo x5000, conserva longitud | No |

---

**Clase: `Monitor Service`**

| Aspecto | Descripción |
|---|---|
| **Ubicación** | `monitor_service.py` |
| **Responsabilidad** | Almacenar y consultar métricas de rendimiento, salud y errores |

**Endpoints expuestos:**
| Endpoint | Método | Descripción |
|---|---|---|
| `/metrics` | GET/POST | Métricas de overhead de rendimiento |
| `/system/metrics` | GET | Métricas de CPU, RAM, disco |
| `/service-health` | POST | Estado de servicios |
| `/db-health` | POST | Estado de motores de BD |
| `/algorithm-ranking` | GET | Ranking de algoritmos |
| `/engine-stats` | GET | Estadísticas por motor |
| `/errors` | GET/POST | Registro de errores |
| `/algorithm-metrics` | POST | Métricas de algoritmos |

**Tablas SQLite:**
| Tabla | Campos principales |
|---|---|
| `metrics` | id, motor_utilizado, masking_mode, tiempo_normal_ms, tiempo_masked_ms, tiempo_encrypted_ms, latency_delta_ms, cpu_overhead, overhead_total_ms, filas_procesadas, timestamp |
| `system_metrics` | id, cpu_percent, ram_used_mb, ram_total_mb, disk_used_gb, disk_total_gb, uptime_seconds, timestamp |
| `db_health` | id, motor, status, latency_ms, error, timestamp |
| `service_health` | id, service_name, status, response_time_ms, timestamp |
| `algorithm_metrics` | id, algorithm_name, avg_time_ms, min_time_ms, max_time_ms, total_executions, timestamp |
| `system_errors` | id, service, error_type, message, timestamp |

---

**Clase: `Auth Module`**

| Aspecto | Descripción |
|---|---|
| **Ubicación** | `auth.py`, `db_usuarios.py` |
| **Responsabilidad** | Gestión de usuarios, sesiones y tokens |

**Funciones de `auth.py`:**
| Función | Descripción |
|---|---|
| `crear_token_sesion(nombre, correo, proveedor)` | Genera token UUID y lo almacena en `SESIONES_ACTIVAS` |
| `obtener_sesion_actual(request)` | Extrae y valida el token de la cookie |
| `revocar_token(token)` | Elimina el token de sesiones activas |
| `agregar_conexion(request, payload)` | Agrega conexión a BD a la sesión del usuario |
| `eliminar_conexion(request, connection_id)` | Elimina conexión de la sesión |
| `obtener_conexion(request, connection_id)` | Obtiene datos de una conexión específica |

**Funciones de `db_usuarios.py`:**
| Función | Descripción |
|---|---|
| `init_db()` | Crea la tabla `users` si no existe |
| `registrar_usuario(nombre, correo, password, proveedor)` | Inserta usuario con hash bcrypt |
| `autenticar_usuario(correo, password)` | Verifica credenciales y retorna usuario |

---

**Clase: `Gobernanza SDM`**

| Aspecto | Descripción |
|---|---|
| **Ubicación** | `governance.py`, `masking_service.py` |
| **Responsabilidad** | Protección/restauración permanente de datos |

**Flujo de protección:**
1. Crear tabla backup `_enmask_backup_[tabla]_[columna]`
2. Leer valores originales
3. Cifrar valores con `cifrar_valor()` (Fernet)
4. Insertar valores cifrados en backup
5. Aplicar enmascaramiento permanente a tabla original
6. Registrar estado "ACTIVA"

**Flujo de restauración:**
1. Leer valores cifrados de tabla backup
2. Descifrar con `descifrar_valor()` (Fernet)
3. Escribir valores originales en tabla principal
4. Registrar estado "INACTIVA"

---

**Clase: `Health Monitor`**

| Aspecto | Descripción |
|---|---|
| **Ubicación** | `health_monitor.py`, `system_metrics.py`, `service_checker.py` |
| **Responsabilidad** | Monitorear salud del sistema, servicios y bases de datos |

**Componentes:**
| Componente | Archivo | Responsabilidad |
|---|---|---|
| System Metrics | `system_metrics.py` | CPU, RAM, disco via `psutil` |
| Service Checker | `service_checker.py` | HTTP health checks a los 3 servicios |
| Database Health | `database_health.py` | Verificación de conectividad a motores BD |
| Health Monitor | `health_monitor.py` | Orquestación de todas las verificaciones |

---

**Diagrama de objetos del sistema:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Diagrama de Objetos — Enmask v2.0             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │  Settings    │    │ DatabaseFactory   │    │ BaseDeDatos   │  │
│  │ (config.py)  │    │                  │    │  (abstracta)  │  │
│  │             │    │ +obtener_motor() │    │               │  │
│  │ APP_NAME    │    └────────┬─────────┘    │ +conectar()   │  │
│  │ DATA_DIR    │             │              │ +obtener_     │  │
│  │ PG_HOST     │             ▼              │  esquema()    │  │
│  │ MYSQL_HOST  │    ┌──────────────────┐    │ +ejecutar_    │  │
│  │ ...         │    │  PostgresDB      │    │  consulta()   │  │
│  └─────────────┘    │  MySQLDB         │    └───────┬───────┘  │
│                     │  SQLiteDB        │            │           │
│                     │  SQLServerDB     │            │           │
│                     │  MongoDB         │            │           │
│                     │  RedisDB         │            │           │
│                     │  Neo4jDB         │            │           │
│                     │  CassandraDB     │            │           │
│                     └──────────────────┘            │           │
│                                                     │           │
│  ┌──────────────────────────────────────────────────┘           │
│  │                                                               │
│  ▼                                                               │
│  ┌─────────────────┐    ┌──────────────────┐                    │
│  │ Masking Engine   │    │ Monitor Service   │                    │
│  │ (masking.py)     │    │(monitor_service.py)│                   │
│  │                 │    │                  │                    │
│  │ +aplicar_       │    │ +registrar_      │                    │
│  │  enmascaramiento│    │  metrica()       │                    │
│  │ +cifrar_valor() │    │ +obtener_        │                    │
│  │ +descifrar_     │    │  metricas()      │                    │
│  │  valor()        │    │ +registrar_      │                    │
│  │ +mask_name()    │    │  error()         │                    │
│  │ +mask_email()   │    │ +obtener_        │                    │
│  │ +mask_phone()   │    │  salud_bd()      │                    │
│  │ +mask_dni()     │    └──────────────────┘                    │
│  │ +mask_generic() │                                             │
│  └─────────────────┘    ┌──────────────────┐                    │
│                         │ Auth Module       │                    │
│                         │ (auth.py)         │                    │
│                         │                  │                    │
│                         │ SESIONES_ACTIVAS │                    │
│                         │ +crear_token()   │                    │
│                         │ +obtener_sesion()│                    │
│                         │ +revocar_token() │                    │
│                         │ +agregar_conexion│                    │
│                         └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

---

#### b) Diagrama de Actividades con objetos

**Actividad: Ejecución de Benchmark de Enmascaramiento**

```
┌─────────────────────────────────────────────────────────────────┐
│         Diagrama de Actividades con Objetos — Benchmark          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐                                                    │
│  │ [Usuario] │                                                    │
│  └────┬─────┘                                                    │
│       ▼                                                           │
│  ┌──────────────────┐                                            │
│  │ :Frontend         │                                            │
│  │ POST /api/v1/     │                                            │
│  │ execute_test      │                                            │
│  └────┬──────────────┘                                            │
│       ▼                                                           │
│  ┌──────────────────┐    ┌─────────────────┐                     │
│  │ :main.py          │    │ :obtener_conexion│                    │
│  │ (API Gateway)     │───►│ (connection_id)  │                    │
│  │                   │    │ → config          │                    │
│  └────┬──────────────┘    └─────────────────┘                     │
│       ▼                                                           │
│  ┌──────────────────┐    ┌─────────────────┐                     │
│  │ :main.py          │    │ :DatabaseFactory │                    │
│  │                   │───►│ .obtener_motor() │                    │
│  │                   │    │ → motor:BaseDatos│                    │
│  └────┬──────────────┘    └─────────────────┘                     │
│       ▼                                                           │
│  ┌──────────────────┐                                            │
│  │ :main.py          │                                            │
│  │ POST /benchmark   │                                            │
│  │ → Masking Service │                                            │
│  └────┬──────────────┘                                            │
│       ▼                                                           │
│  ┌──────────────────┐    ┌─────────────────┐                     │
│  │ :masking_service  │    │ :motor           │                    │
│  │                   │───►│ .ejecutar_consulta│                   │
│  │ time.perf_counter │    │ → datos_crudos    │                   │
│  │ _ns() → t_inicio  │    └─────────────────┘                     │
│  └────┬──────────────┘                                            │
│       ▼                                                           │
│  ┌──────────────────┐    ┌─────────────────┐                     │
│  │ :masking_service  │    │ :masking.py      │                    │
│  │                   │───►│ .aplicar_        │                    │
│  │ time.perf_counter │    │  enmascaramiento │                    │
│  │ _ns() → t_mask    │    │ → datos_masked   │                    │
│  └────┬──────────────┘    └─────────────────┘                     │
│       ▼                                                           │
│  ┌──────────────────┐    ┌─────────────────┐                     │
│  │ :masking_service  │    │ :masking.py      │                    │
│  │                   │───►│ .cifrar_valor()  │                    │
│  │ time.perf_counter │    │ → datos_encrypted│                    │
│  │ _ns() → t_encrypt │    └─────────────────┘                     │
│  └────┬──────────────┘                                            │
│       ▼                                                           │
│  ┌──────────────────┐                                            │
│  │ :masking_service  │                                            │
│  │ Calcular métricas:│                                            │
│  │ tiempo_normal_ms  │                                            │
│  │ tiempo_mask_ms    │                                            │
│  │ tiempo_encrypted  │                                            │
│  │ latency_delta     │                                            │
│  │ cpu_overhead      │                                            │
│  └────┬──────────────┘                                            │
│       ▼                                                           │
│  ┌──────────────────┐    ┌─────────────────┐                     │
│  │ :main.py          │    │ :Monitor Service │                    │
│  │                   │───►│ POST /metrics    │                    │
│  │ Calcular overhead │    │ → SQLite         │                    │
│  │ _total_ms         │    └─────────────────┘                     │
│  └────┬──────────────┘                                            │
│       ▼                                                           │
│  ┌──────────────────┐                                            │
│  │ :main.py          │                                            │
│  │ Retornar al       │                                            │
│  │ Frontend con:     │                                            │
│  │ - data            │                                            │
│  │ - métricas        │                                            │
│  └────┬──────────────┘                                            │
│       ▼                                                           │
│  ┌──────────────────┐                                            │
│  │ :Frontend         │                                            │
│  │ Mostrar tabla     │                                            │
│  │ comparativa +     │                                            │
│  │ gráficos overhead │                                            │
│  └──────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

**Actividad: Gobernanza SDM — Activar Protección**

```
┌─────────────────────────────────────────────────────────────────┐
│         Diagrama de Actividades con Objetos — SDM Protect        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐                                                │
│  │ [Admin]       │                                                │
│  └────┬─────────┘                                                │
│       ▼                                                           │
│  ┌──────────────────┐                                            │
│  │ :main.py          │                                            │
│  │ POST /governance/ │                                            │
│  │ protect           │                                            │
│  └────┬──────────────┘                                            │
│       ▼                                                           │
│  ┌──────────────────┐                                            │
│  │ :main.py          │                                            │
│  │ Verificar motor   │                                            │
│  │ ∈ SDM_DISPONIBLES │                                            │
│  └────┬──────────────┘                                            │
│       │                                                           │
│       ├──── [NO] ──► Error 400                                   │
│       │                                                           │
│       ▼                                                           │
│  ┌──────────────────┐    ┌─────────────────┐                     │
│  │ :main.py          │    │ :Masking Service │                    │
│  │                   │───►│ POST /protect    │                    │
│  └────┬──────────────┘    └────────┬────────┘                     │
│       │                            ▼                               │
│       │                   ┌─────────────────┐                     │
│       │                   │ :Masking Service │                    │
│       │                   │ Crear tabla      │                    │
│       │                   │ backup:          │                    │
│       │                   │ _enmask_backup_  │                    │
│       │                   │ [tabla]_[col]    │                    │
│       │                   └────────┬────────┘                     │
│       │                            ▼                               │
│       │                   ┌─────────────────┐                     │
│       │                   │ :masking.py      │                    │
│       │                   │ .cifrar_valor()  │                    │
│       │                   │ Cada valor →     │                    │
│       │                   │ Fernet(valor)    │                    │
│       │                   └────────┬────────┘                     │
│       │                            ▼                               │
│       │                   ┌─────────────────┐                     │
│       │                   │ :Masking Service │                    │
│       │                   │ Insertar backup  │                    │
│       │                   │ Aplicar masking  │                    │
│       │                   │ permanente       │                    │
│       │                   └────────┬────────┘                     │
│       │                            ▼                               │
│       ▼                                                           │
│  ┌──────────────────┐                                            │
│  │ :main.py          │                                            │
│  │ Retornar          │                                            │
│  │ {estado: "ACTIVA"}│                                            │
│  └──────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

#### c) Diagrama de Secuencia

**Secuencia: Login de Usuario**

```
┌─────────────────────────────────────────────────────────────────┐
│              Diagrama de Secuencia — Login                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  :Frontend        :main.py         :db_usuarios    :auth.py     │
│      │                │                  │              │        │
│      │  POST /api/    │                  │              │        │
│      │  login         │                  │              │        │
│      │ (correo,       │                  │              │        │
│      │  password)     │                  │              │        │
│      │───────────────►│                  │              │        │
│      │                │                  │              │        │
│      │                │  autenticar_     │              │        │
│      │                │  usuario(correo, │              │        │
│      │                │  password)       │              │        │
│      │                │─────────────────►│              │        │
│      │                │                  │              │        │
│      │                │                  │ Buscar por   │        │
│      │                │                  │ correo en    │        │
│      │                │                  │ tabla users  │        │
│      │                │                  │─────┐        │        │
│      │                │                  │     │        │        │
│      │                │                  │◄────┘        │        │
│      │                │                  │              │        │
│      │                │                  │ Verificar    │        │
│      │                │                  │ bcrypt       │        │
│      │                │                  │ (password,   │        │
│      │                │                  │  hash)       │        │
│      │                │                  │─────┐        │        │
│      │                │                  │     │        │        │
│      │                │                  │◄────┘        │        │
│      │                │                  │              │        │
│      │                │  usuario / None  │              │        │
│      │                │◄─────────────────│              │        │
│      │                │                  │              │        │
│      │                │  crear_token_    │              │        │
│      │                │  sesion(nombre,  │              │        │
│      │                │  correo,         │              │        │
│      │                │  proveedor)      │              │        │
│      │                │─────────────────────────────────►│       │
│      │                │                  │              │        │
│      │                │                  │  UUID token  │        │
│      │                │                  │  Almacenar   │        │
│      │                │                  │  en SESIONES │        │
│      │                │                  │  _ACTIVAS    │        │
│      │                │                  │  ────┐       │        │
│      │                │                  │      │       │        │
│      │                │                  │  ◄───┘       │        │
│      │                │                  │              │        │
│      │                │  token           │              │        │
│      │                │◄────────────────────────────────│        │
│      │                │                  │              │        │
│      │  Set-Cookie:   │                  │              │        │
│      │  session_token │                  │              │        │
│      │  (httponly)     │                  │              │        │
│      │  + JSON        │                  │              │        │
│      │  {message,     │                  │              │        │
│      │   nombre}      │                  │              │        │
│      │◄───────────────│                  │              │        │
│      │                │                  │              │        │
│      ▼                ▼                  ▼              ▼        │
└─────────────────────────────────────────────────────────────────┘
```

---

**Secuencia: Ejecución de Benchmark**

```
┌─────────────────────────────────────────────────────────────────┐
│     Diagrama de Secuencia — Benchmark de Enmascaramiento         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ :Frontend  :main.py   :MaskingSvc  :motor:BD  :masking.py  :MonitorSvc│
│    │           │           │           │           │           │  │
│    │ POST      │           │           │           │           │  │
│    │ /execute  │           │           │           │           │  │
│    │ _test     │           │           │           │           │  │
│    │──────────►│           │           │           │           │  │
│    │           │           │           │           │           │  │
│    │           │ POST      │           │           │           │  │
│    │           │ /benchmark│           │           │           │  │
│    │           │──────────►│           │           │           │  │
│    │           │           │           │           │           │  │
│    │           │           │ t_inicio  │           │           │  │
│    │           │           │ =perf_ns()│           │           │  │
│    │           │           │─────┐     │           │           │  │
│    │           │           │     │     │           │           │  │
│    │           │           │◄────┘     │           │           │  │
│    │           │           │           │           │           │  │
│    │           │           │ ejecutar_ │           │           │  │
│    │           │           │ consulta()│           │           │  │
│    │           │           │──────────►│           │           │  │
│    │           │           │           │           │           │  │
│    │           │           │ datos     │           │           │  │
│    │           │           │ crudos    │           │           │  │
│    │           │           │◄──────────│           │           │  │
│    │           │           │           │           │           │  │
│    │           │           │ t_normal  │           │           │  │
│    │           │           │ =perf_ns()│           │           │  │
│    │           │           │─────┐     │           │           │  │
│    │           │           │     │     │           │           │  │
│    │           │           │◄────┘     │           │           │  │
│    │           │           │           │           │           │  │
│    │           │           │ aplicar_  │           │           │  │
│    │           │           │ enmascara-│           │           │  │
│    │           │           │ miento()  │           │           │  │
│    │           │           │──────────────────────►│           │  │
│    │           │           │           │           │           │  │
│    │           │           │ datos     │           │           │  │
│    │           │           │ masked    │           │           │  │
│    │           │           │◄──────────────────────│           │  │
│    │           │           │           │           │           │  │
│    │           │           │ t_mask    │           │           │  │
│    │           │           │ =perf_ns()│           │           │  │
│    │           │           │           │           │           │  │
│    │           │           │ cifrar_   │           │           │  │
│    │           │           │ valor()   │           │           │  │
│    │           │           │──────────────────────►│           │  │
│    │           │           │           │           │           │  │
│    │           │           │ datos     │           │           │  │
│    │           │           │ encrypted │           │           │  │
│    │           │           │◄──────────────────────│           │  │
│    │           │           │           │           │           │  │
│    │           │           │ t_encrypt │           │           │  │
│    │           │           │ =perf_ns()│           │           │  │
│    │           │           │           │           │           │  │
│    │           │ Calcular  │           │           │           │  │
│    │           │ overhead  │           │           │           │  │
│    │           │◄──────────│           │           │           │  │
│    │           │           │           │           │           │  │
│    │           │ POST      │           │           │           │  │
│    │           │ /metrics  │           │           │           │  │
│    │           │──────────────────────────────────────────────►│  │
│    │           │           │           │           │     SQLite│  │
│    │           │ OK        │           │           │           │  │
│    │           │◄──────────────────────────────────────────────│  │
│    │           │           │           │           │           │  │
│    │ JSON:     │           │           │           │           │  │
│    │ data +    │           │           │           │           │  │
│    │ métricas  │           │           │           │           │  │
│    │◄──────────│           │           │           │           │  │
│    │           │           │           │           │           │  │
│    ▼           ▼           ▼           ▼           ▼           ▼  │
└─────────────────────────────────────────────────────────────────┘
```

---

#### d) Diagrama de Clases

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Diagrama de Clases — Enmask v2.0                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────┐                                     │
│  │         <<abstract>>            │                                     │
│  │         BaseDeDatos             │                                     │
│  ├─────────────────────────────────┤                                     │
│  │ - credenciales: Dict[str, Any]  │                                     │
│  ├─────────────────────────────────┤                                     │
│  │ + conectar(): Connection        │                                     │
│  │ + obtener_esquema(): Dict       │                                     │
│  │ + ejecutar_consulta(): List     │                                     │
│  └──────────────┬──────────────────┘                                     │
│                 │                                                         │
│    ┌────────────┼────────────┬──────────────┬──────────────┐             │
│    │            │            │              │              │             │
│    ▼            ▼            ▼              ▼              ▼             │
│ ┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│ │Postgres│ │ MySQL  │ │  SQLite  │ │SQLServer │ │ MongoDB  │           │
│ │   DB   │ │   DB   │ │    DB    │ │    DB    │ │          │           │
│ ├────────┤ ├────────┤ ├──────────┤ ├──────────┤ ├──────────┤           │
│ │        │ │        │ │          │ │          │ │          │           │
│ ├────────┤ ├────────┤ ├──────────┤ ├──────────┤ ├──────────┤           │
│ │+conectar│ │+conectar│ │+conectar │ │+conectar │ │+conectar │          │
│ │+obtener_│ │+obtener_│ │+obtener_ │ │+obtener_ │ │+obtener_ │          │
│ │ esquema │ │ esquema │ │ esquema  │ │ esquema  │ │ esquema  │          │
│ │+ejecutar│ │+ejecutar│ │+ejecutar │ │+ejecutar │ │+ejecutar │          │
│ └────────┘ └────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                           │
│    ┌────────────┼────────────┐                                           │
│    │            │            │                                           │
│    ▼            ▼            ▼                                           │
│ ┌────────┐ ┌────────┐ ┌──────────┐                                      │
│ │ Redis  │ │ Neo4j  │ │Cassandra │                                      │
│ │   DB   │ │   DB   │ │    DB    │                                      │
│ ├────────┤ ├────────┤ ├──────────┤                                      │
│ │        │ │        │ │          │                                      │
│ ├────────┤ ├────────┤ ├──────────┤                                      │
│ │+conectar│ │+conectar│ │+conectar │                                     │
│ │+obtener_│ │+obtener_│ │+obtener_ │                                     │
│ │ esquema │ │ esquema │ │ esquema  │                                     │
│ │+ejecutar│ │+ejecutar│ │+ejecutar │                                     │
│ └────────┘ └────────┘ └──────────┘                                      │
│                                                                           │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐     │
│  │     DatabaseFactory         │    │         Settings             │     │
│  ├─────────────────────────────┤    ├─────────────────────────────┤     │
│  │                             │    │ +APP_NAME: str              │     │
│  ├─────────────────────────────┤    │ +DEBUG: bool                │     │
│  │ +obtener_motor(motor,       │    │ +DATA_DIR: str              │     │
│  │  credenciales): BaseDeDatos │    │ +PG_HOST: str               │     │
│  └─────────────────────────────┘    │ +MYSQL_HOST: str            │     │
│                                     │ +MONGO_URI: str             │     │
│  ┌─────────────────────────────┐    │ +REDIS_HOST: str            │     │
│  │      MaskingEngine          │    │ +NEO4J_URI: str             │     │
│  │       (masking.py)          │    └─────────────────────────────┘     │
│  ├─────────────────────────────┤                                        │
│  │ -FERNET_KEY: bytes          │    ┌─────────────────────────────┐     │
│  │ -cipher_suite: Fernet       │    │       MonitorService        │     │
│  ├─────────────────────────────┤    │    (monitor_service.py)     │     │
│  │ +aplicar_enmascaramiento(   │    ├─────────────────────────────┤     │
│  │  datos, reglas): List       │    │ -db_path: str               │     │
│  │ +cifrar_valor(texto): str   │    ├─────────────────────────────┤     │
│  │ +descifrar_valor(token):str │    │ +registrar_metrica(): void  │     │
│  │ +mask_name(value): str      │    │ +obtener_metricas(): List   │     │
│  │ +mask_email(value): str     │    │ +registrar_error(): void    │     │
│  │ +mask_phone(value): str     │    │ +obtener_salud_bd(): List   │     │
│  │ +mask_dni(value): str       │    │ +ranking_algoritmos(): List │     │
│  │ +mask_generic(value): str   │    └─────────────────────────────┘     │
│  │ +academic_mask_value(): str │                                        │
│  └─────────────────────────────┘    ┌─────────────────────────────┐     │
│                                     │        AuthModule            │     │
│  ┌─────────────────────────────┐    │       (auth.py)             │     │
│  │     GovernanceSDM           │    ├─────────────────────────────┤     │
│  │      (governance.py)        │    │ -SESIONES_ACTIVAS: Dict     │     │
│  ├─────────────────────────────┤    ├─────────────────────────────┤     │
│  │                             │    │ +crear_token_sesion(): str  │     │
│  ├─────────────────────────────┤    │ +obtener_sesion_actual():   │     │
│  │ +activar_proteccion(): void │    │  Dict                       │     │
│  │ +restaurar_datos(): void    │    │ +revocar_token(): void      │     │
│  │ +consultar_estado(): Dict   │    │ +agregar_conexion(): str    │     │
│  └─────────────────────────────┘    │ +eliminar_conexion(): void  │     │
│                                     │ +obtener_conexion(): Dict   │     │
│  ┌─────────────────────────────┐    └─────────────────────────────┘     │
│  │      HealthMonitor          │                                        │
│  │   (health_monitor.py)       │    ┌─────────────────────────────┐     │
│  ├─────────────────────────────┤    │         User                 │     │
│  │                             │    │       (db_usuarios.py)       │     │
│  ├─────────────────────────────┤    ├─────────────────────────────┤     │
│  │ +verificar_sistema(): Dict  │    │ +id: INTEGER (PK)           │     │
│  │ +verificar_servicios(): Dict│    │ +nombre_completo: TEXT      │     │
│  │ +verificar_bd(): Dict       │    │ +correo: TEXT (UNIQUE)      │     │
│  └─────────────────────────────┘    │ +password_hash: TEXT        │     │
│                                     │ +proveedor: TEXT            │     │
│  ┌─────────────────────────────┐    │ +fecha_creacion: DATETIME   │     │
│  │      Metrics (SQLite)        │    ├─────────────────────────────┤     │
│  ├─────────────────────────────┤    │ +registrar(): void          │     │
│  │ +id: INTEGER (PK)           │    │ +autenticar(): Dict         │     │
│  │ +motor_utilizado: TEXT      │    └─────────────────────────────┘     │
│  │ +masking_mode: TEXT         │                                        │
│  │ +tiempo_normal_ms: REAL     │                                        │
│  │ +tiempo_masked_ms: REAL     │                                        │
│  │ +tiempo_encrypted_ms: REAL  │                                        │
│  │ +overhead_total_ms: REAL    │                                        │
│  │ +filas_procesadas: INTEGER  │                                        │
│  │ +timestamp: DATETIME        │                                        │
│  └─────────────────────────────┘                                        │
│                                                                           │
│  RELACIONES:                                                              │
│  • DatabaseFactory ──creates──► BaseDeDatos                               │
│  • API Gateway ──uses──► DatabaseFactory                                  │
│  • API Gateway ──calls──► MaskingService                                  │
│  • API Gateway ──calls──► MonitorService                                  │
│  • MaskingService ──uses──► MaskingEngine                                 │
│  • MaskingService ──uses──► GovernanceSDM                                 │
│  • GovernanceSDM ──uses──► MaskingEngine                                  │
│  • MonitorService ──persists──► Metrics (SQLite)                          │
│  • AuthModule ──persists──► User (SQLite)                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## CONCLUSIONES

1. El FD03 ha especificado de manera detallada los **25 requerimientos funcionales** y **20 requerimientos no funcionales** del sistema Enmask v2.0, proporcionando la base técnica para la implementación.

2. Los **8 casos de uso** documentados cubren los flujos principales del sistema: autenticación, conexión a BD, enmascaramiento, cifrado, gobernanza SDM y monitoreo.

3. El **diagrama de clases** refleja fielmente la arquitectura implementada en el código fuente, con el patrón Factory en `DatabaseFactory`, el módulo de enmascaramiento en `masking.py` y el servicio de monitoreo en `monitor_service.py`.

4. Las **15 reglas de negocio** definidas garantizan la integridad, seguridad y consistencia de las operaciones del sistema.

5. El **análisis de objetos** de los 7 componentes principales (BaseDeDatos, DatabaseFactory, MaskingEngine, MonitorService, AuthModule, GovernanceSDM, HealthMonitor) demuestra una arquitectura modular y extensible.

6. Los diagramas UML (actividades con objetos, secuencia, clases) representan con precisión los flujos de datos y control del sistema, sirviendo como referencia técnica para el equipo de desarrollo.

7. El sistema es viable desde todas las dimensiones evaluadas (técnica, económica, legal, social, ambiental) y los requerimientos especificados están alineados con los objetivos del curso de Bases de Datos II.

## RECOMENDACIONES

1. Priorizar la implementación de los requerimientos de prioridad **Alta** (RF-001 a RF-010, RF-013 a RF-016, RF-018 a RF-020, RF-025) para garantizar un MVP funcional.

2. Validar los diagramas UML con el docente antes de proceder a la codificación, realizando ajustes según la retroalimentación recibida.

3. Mantener la trazabilidad entre requerimientos y código fuente, actualizando este documento cuando se implementen cambios.

4. Implementar pruebas unitarias para cada requerimiento funcional, especialmente los algoritmos de enmascaramiento (redaccion, hashing, encriptacion, fpe).

5. Documentar las decisiones técnicas tomadas durante la implementación para facilitar el mantenimiento futuro.

6. Realizar pruebas de integración con los 7 motores de bases de datos desde las primeras fases del desarrollo.

## BIBLIOGRAFÍA

- FastAPI. (2024). FastAPI Documentation. Recuperado de https://fastapi.tiangolo.com
- React. (2024). React Documentation. Recuperado de https://react.dev
- PostgreSQL. (2024). PostgreSQL Documentation. Recuperado de https://www.postgresql.org/docs
- MongoDB. (2024). MongoDB Documentation. Recuperado de https://docs.mongodb.com
- Docker. (2024). Docker Documentation. Recuperado de https://docs.docker.com
- GDPR. (2016). Reglamento General de Protección de Datos (UE) 2016/679.
- Ley N° 29733. (2011). Ley de Protección de Datos Personales - Perú.
- OWASP. (2024). OWASP Top 10. Recuperado de https://owasp.org/Top10
- Martin, R. C. (2017). Clean Architecture: A Craftsman's Guide to Software Structure and Design. Prentice Hall.
- Evans, E. (2003). Domain-Driven Design: Tackling Complexity in the Heart of Software. Addison-Wesley.

## WEBGRAFÍA

- PostgreSQL pgcrypto. (2024). Recuperado de https://www.postgresql.org/docs/current/pgcrypto.html
- MongoDB Aggregation Pipeline. (2024). Recuperado de https://docs.mongodb.com/manual/core/aggregation-pipeline
- Redis Lua Scripting. (2024). Recuperado de https://redis.io/docs/manual/programmability/eval-intro
- Neo4j APOC Library. (2024). Recuperado de https://neo4j.com/docs/apoc
- SQL Server Encryption. (2024). Recuperado de https://docs.microsoft.com/en-us/sql/relational-databases/security/encryption
- Cassandra CQL. (2024). Recuperado de https://cassandra.apache.org/doc/latest/cassandra/cql
- Chart.js Documentation. (2024). Recuperado de https://www.chartjs.org/docs/
- Tailwind CSS Documentation. (2024). Recuperado de https://tailwindcss.com/docs
- Fernet Specification. (2024). Recuperado de https://cryptography.io/en/latest/fernet/
- psutil Documentation. (2024). Recuperado de https://psutil.readthedocs.io/

---

*Documento FD03 — Informe de Especificación de Requerimientos*
*Sistema Enmask v2.0 — Multi-DB Masking & Performance Overhead Monitor*
*Versión 1.0 — Junio 2026*
