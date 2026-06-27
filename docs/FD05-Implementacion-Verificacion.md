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

# FD05 — Informe de Implementación y Verificación

## Sistema Enmask v2.0

### Multi-DB Masking & Performance Overhead Monitor

---

## ÍNDICE GENERAL

| Nro | Sección | Pág |
|---|---|---|
| **1** | **ANTECEDENTES** | **1** |
| **2** | **PLANTEAMIENTO DEL PROBLEMA** | **4** |
| 2.a | Problema | 4 |
| 2.b | Justificación | 5 |
| 2.c | Alcance | 6 |
| **3** | **OBJETIVOS** | **6** |
| 3.1 | Objetivo General | 6 |
| 3.2 | Objetivos Específicos | 6 |
| **4** | **MARCO TEÓRICO** | **7** |
| 4.1 | Enmascaramiento de Datos (Data Masking) | 7 |
| 4.2 | Cifrado que Preserva el Formato (FPE) | 8 |
| 4.3 | Gobernanza de Datos Estáticos (SDM) | 8 |
| 4.4 | Monitoreo de Rendimiento y Overhead | 9 |
| 4.5 | Arquitectura de Microservicios | 9 |
| 4.6 | Normativas de Protección de Datos | 10 |
| **5** | **DESARROLLO DE LA SOLUCIÓN** | **9** |
| 5.a | Análisis de Factibilidad | 9 |
| 5.b | Tecnología de Desarrollo | 12 |
| 5.c | Metodología de Implementación | 14 |
| **6** | **CRONOGRAMA** | **11** |
| **7** | **PRESUPUESTO** | **12** |
| **8** | **CONCLUSIONES** | **13** |
| **9** | **RECOMENDACIONES** | **14** |
| **10** | **BIBLIOGRAFÍA** | **15** |
| **11** | **ANEXOS** | **16** |
| | Anexo 01 — Informe de Factibilidad (FD01) | 16 |
| | Anexo 02 — Documento de Visión (FD02) | 16 |
| | Anexo 03 — Documento SRS (FD03) | 16 |
| | Anexo 04 — Documento SAD (FD04) | 16 |
| | Anexo 05 — Manuales y otros documentos | 16 |

---

## 1. ANTECEDENTES

El presente documento constituye el quinto entregable formal del proyecto **Enmask v2.0**, denominado **FD05 — Informe de Implementación y Verificación**, el cual documenta la fase de construcción, configuración, despliegue y validación del sistema desarrollado.

El proyecto **Enmask v2.0** nace como respuesta a la necesidad creciente de proteger datos sensibles (PII — Personally Identifiable Information) en entornos no productivos dentro de las organizaciones. Las empresas manejan grandes volúmenes de información personal que deben ser resguardados tanto en bases de datos productivas como en copias utilizadas para desarrollo, pruebas y análisis. Las soluciones tradicionales de enmascaramiento presentan limitaciones significativas en cuanto a rendimiento, cobertura multi-motor, auditoría y cumplimiento normativo.

El sistema fue conceptualizado como una plataforma de **SecOps / DBA Tools** que fusiona un motor de enmascaramiento dinámico de datos con un monitor de rendimiento e infraestructura. La propuesta de valor principal no es solo ocultar datos, sino **medir y graficar cuantitativamente el "impuesto de rendimiento" (overhead)** que la seguridad introduce al realizar consultas en tiempo real sobre diferentes motores de bases de datos.

El proyecto se sustenta en los siguientes documentos previos:

- **FD01 — Informe de Factibilidad:** Evaluó la viabilidad técnica, económica, legal, social y ambiental del proyecto, concluyendo que todas las dimensiones eran favorables.
- **FD02 — Documento de Visión:** Definió la visión, misión, alcance, capacidades y restricciones del sistema, estableciendo los objetivos de negocio y diseño.
- **FD03 — Informe de Especificación de Requerimientos (SRS):** Especificó 25 requerimientos funcionales, 20 no funcionales, 15 reglas de negocio, diagramas UML (casos de uso, actividades, secuencia, clases) y el análisis de objetos del sistema.
- **FD04 — Diseño de Arquitectura (SAD):** Definió la arquitectura software aplicando el modelo de vistas "4+1" de Philippe Kruchten, incluyendo las vistas lógica, de procesos, de desarrollo, física y de casos de uso.

En este FD05, se procede a documentar la **implementación concreta** del sistema, incluyendo el análisis de factibilidad detallado, las tecnologías utilizadas, la metodología de implementación, el cronograma de desarrollo, el presupuesto, así como las conclusiones y recomendaciones derivadas del proceso de construcción y verificación del sistema.

---

## 2. PLANTEAMIENTO DEL PROBLEMA

### 2.a. Problema

Las organizaciones contemporáneas enfrentan un desafío crítico en la protección de datos sensibles dentro de sus entornos de desarrollo, pruebas y análisis. El problema se manifiesta en múltiples dimensiones:

**1. Procesamiento ineficiente del enmascaramiento:**
Las soluciones tradicionales de enmascaramiento operan en la capa de aplicación, lo que genera cuellos de botella significativos al mover grandes volúmenes de datos por la red. Este enfoque introduce latencia adicional que puede multiplicar por 5 o más el tiempo de respuesta de las consultas, impactando directamente la productividad de los equipos de desarrollo y análisis.

**2. Fragmentación de herramientas por motor de BD:**
Cada motor de base de datos (PostgreSQL, MySQL, SQL Server, MongoDB, Redis, Neo4j, entre otros) requiere scripts específicos de enmascaramiento, lo que duplica esfuerzos, introduce inconsistencias en la protección y genera una carga operativa significativa para los DBAs. Una organización típica puede utilizar 4 o más motores diferentes, multiplicando exponencialmente la complejidad.

**3. Ausencia de métricas cuantitativas de rendimiento:**
No existe en el mercado una herramienta que permita medir de forma precisa y automatizada el overhead que la seguridad introduce en las operaciones de base de datos. Las organizaciones toman decisiones sobre técnicas de enmascaramiento sin contar con datos objetivos de rendimiento, lo que puede llevar a implementaciones ineficientes.

**4. Riesgos de seguridad y cumplimiento normativo:**
La falta de un sistema centralizado de gestión de llaves criptográficas, auditoría de accesos y trazabilidad de operaciones expone a las organizaciones a fugas de datos y sanciones regulatorias. Las prácticas actuales no satisfacen los requisitos de GDPR (Art. 32), PCI-DSS ni la Ley N° 29733 de Protección de Datos Personales del Perú.

**5. Incumplimiento normativo:**
Las soluciones existentes en el mercado son de alto costo (IBM Optim, Delphix, Informatica) o de complejidad operativa elevada, lo que las hace inaccesibles para organizaciones pequeñas y medianas, así como para entornos académicos.

### 2.b. Justificación

La justificación del proyecto Enmask v2.0 se fundamenta en tres pilares fundamentales:

**Justificación Técnica:**
El sistema propuesto aborda las limitaciones técnicas de las soluciones existentes mediante una arquitectura de microservicios desacoplada que delega el procesamiento de enmascaramiento a los motores nativos de bases de datos. Este enfoque garantiza un rendimiento superior al evitar el movimiento innecesario de datos por la red. La implementación del patrón Factory permite la extensibilidad del sistema para soportar nuevos motores sin modificar la lógica central.

**Justificación Económica:**
A diferencia de soluciones comerciales que pueden costar entre $50,000 y $500,000 USD anuales, Enmask v2.0 utiliza exclusivamente tecnologías de código abierto (Python, FastAPI, SQLite, Docker), lo que reduce los costos de licenciamiento a cero. El costo total de implementación se estima en aproximadamente $10 USD, correspondientes únicamente al despliegue en la nube (Render).

**Justificación Académica:**
El proyecto contribuye al campo de la seguridad de datos y la ingeniería de bases de datos al proporcionar una herramienta educativa que permite a estudiantes y profesionales comprender los conceptos de enmascaramiento, cifrado y monitoreo de rendimiento de manera práctica. La documentación completa del proyecto sirve como referencia para futuras investigaciones y desarrollos.

**Justificación Social:**
El sistema promueve la cultura de protección de datos personales en las organizaciones, contribuyendo al cumplimiento normativo y a la generación de confianza en los entornos digitales. La disponibilidad como herramienta de código abierto permite su adopción por organizaciones con recursos limitados.

### 2.c. Alcance

#### Alcance Incluido

| Área | Elementos Entregables |
|---|---|
| **Motores de BD Soportados** | PostgreSQL, MySQL, SQL Server, SQLite, MongoDB, Redis, Neo4j (7 motores) |
| **Algoritmos de Enmascaramiento** | Redacción (X), Hashing (SHA-256), Encriptación (Fernet/AES-128-CBC), FPE simulado |
| **Gobernanza SDM** | Protección permanente (SDM), restauración de datos, backup cifrado con Fernet |
| **Monitoreo de Rendimiento** | Delta de latencia (ms), consumo de CPU, eficiencia de algoritmos, ranking comparativo |
| **Monitoreo de Infraestructura** | CPU, RAM, disco, uptime, salud de servicios y motores BD |
| **Seguridad** | Login bcrypt, Google OAuth2, cookies HTTP-only, gestión de claves Fernet |
| **Dashboard de Observabilidad** | Security Dashboard, Health Monitor, Database Observatory, Algorithm Analytics |
| **Despliegue** | Docker Compose (local), Render (nube), variables de entorno configurables |

#### Alcance Excluido

| Área | Elementos Excluidos |
|---|---|
| Enmascaramiento dinámico (proxy SQL) | No se implementa enmascaramiento en tiempo real por proxy |
| Motores adicionales | Oracle, DB2, Firebird, Couchbase, Elasticsearch |
| Anonimización estadística | k-anonimidad, l-diversidad, privacidad diferencial |
| Autenticación LDAP/Active Directory | Solo login local y Google OAuth2 |
| Alertas por correo/SMS | No se implementa sistema de notificaciones externas |
| CLI (interfaz de línea de comandos) | Solo interfaz web y API REST |

---

## 3. OBJETIVOS

### 3.1. Objetivo General

Desarrollar e implementar una plataforma web de **enmascaramiento estático de datos y monitoreo de rendimiento** que permita a las organizaciones proteger información sensible (PII) en entornos no productivos, operando de manera unificada sobre 7 motores de bases de datos, y cuantificando el impacto de rendimiento (overhead) que las técnicas de seguridad introducen en las operaciones de consulta.

### 3.2. Objetivos Específicos

| Nro | Objetivo Específico | Indicador de Verificación |
|---|---|---|
| OE-01 | Implementar una arquitectura de microservicios desacoplada con API Gateway, Masking Service y Monitor Service | 3 servicios funcionando independientemente en puertos 8000, 8001, 8002 |
| OE-02 | Desarrollar un DatabaseFactory que soporte 7 motores de bases de datos (PostgreSQL, MySQL, SQL Server, SQLite, MongoDB, Redis, Neo4j) | Conexión exitosa a los 7 motores desde una interfaz unificada |
| OE-03 | Implementar 4 algoritmos de enmascaramiento (redacción, hashing, encriptación, FPE) con medición precisa de tiempos | Benchmark ejecutado con `time.perf_counter_ns()` y resultados en ms |
| OE-04 | Desarrollar un sistema de gobernanza SDM que permita la protección permanente con backup cifrado y restauración de datos | Activar/restaurar SDM en motores soportados con backup Fernet |
| OE-05 | Implementar un monitor de rendimiento que mida el overhead de seguridad (latencia, CPU, eficiencia de algoritmos) | Dashboard con métricas en tiempo real actualizadas cada 5 segundos |
| OE-06 | Implementar un sistema de autenticación seguro con bcrypt y Google OAuth2 | Login funcional con hash bcrypt y flujo OAuth2 completo |
| OE-07 | Contenerizar el sistema completo con Docker Compose para despliegue local y en nube (Render) | `docker compose up -d` levanta todos los servicios correctamente |
| OE-08 | Documentar el sistema con diagramas UML completos (casos de uso, secuencia, clases, despliegue) | Diagramas en FD03 y FD04 validados e implementados |

---

## 4. MARCO TEÓRICO

### 4.1. Enmascaramiento de Datos (Data Masking)

El enmascaramiento de datos es una técnica de seguridad de la información que consiste en crear una versión estructuralmente similar pero modificada de los datos originales, de manera que la información sensible sea reemplazada por datos ficticios pero realistas. El objetivo es proteger la información de identificación personal (PII) mientras se mantiene la utilidad de los datos para fines de desarrollo, pruebas y análisis.

**Tipos de enmascaramiento implementados en Enmask v2.0:**

| Técnica | Descripción | Reversible | Rendimiento |
|---|---|---|---|
| **Redacción** | Reemplaza cada carácter por "X" | No | Muy rápido (O(n)) |
| **Hashing SHA-256** | Genera hash irreversible del valor | No | Rápido (O(n)) |
| **Encriptación Fernet** | Cifrado simétrico AES-128-CBC | Sí (con clave) | Moderado |
| **FPE simulado** | Hash iterativo x5000 que conserva longitud | No | Lento (O(n×5000)) |

### 4.2. Cifrado que Preserva el Formato (FPE)

El Format-Preserving Encryption (FPE) es una técnica criptográfica que cifra datos de manera que el resultado mantenga el mismo formato que el texto original. Por ejemplo, si se cifra un número de 8 dígitos, el resultado será otro número de 8 dígitos.

En Enmask v2.0 se implementa un **FPE simulado** mediante hashing iterativo SHA-256 (5000 iteraciones), que conserva la longitud del valor original. Esta aproximación no es un FPE estándar real (como FF1 o FF3 de NIST), sino una técnica educativa que demuestra el concepto con mayor carga de CPU.

### 4.3. Gobernanza de Datos Estáticos (SDM)

El Static Data Masking (SDM) es un enfoque de enmascaramiento donde los datos se transforman de manera permanente en la base de datos destino. A diferencia del enmascaramiento dinámico (que opera en tiempo real mediante proxies), el SDM modifica físicamente los datos almacenados.

El sistema Enmask v2.0 implementa un flujo de gobernanza SDM completo:

1. **Creación de backup cifrado:** Antes de modificar los datos originales, se crea una tabla de backup (`_enmask_backup_[tabla]_[columna]`) donde se almacenan los valores originales cifrados con Fernet.
2. **Aplicación de enmascaramiento permanente:** Los datos originales son reemplazados por los valores enmascarados según el algoritmo seleccionado.
3. **Restauración de datos:** Mediante la clave Fernet, se pueden descifrar los valores del backup y restaurar los datos originales.

### 4.4. Monitoreo de Rendimiento y Overhead

El **overhead de rendimiento** se define como el costo adicional en términos de tiempo de procesamiento que introduce una funcionalidad de seguridad (enmascaramiento, cifrado) en las operaciones de base de datos.

Enmask v2.0 mide tres métricas clave:

| Métrica | Descripción | Fórmula |
|---|---|---|
| **Delta de Latencia (ms)** | Diferencia entre tiempo de consulta cruda y tiempo con enmascaramiento | `tiempo_masked - tiempo_normal` |
| **Consumo de CPU por Seguridad** | Porcentaje del procesamiento atribuible al enmascaramiento | `cpu_overhead` |
| **Eficiencia de Algoritmos** | Comparativa de rendimiento entre técnicas simples y complejas | Ranking por `avg_time_ms` |

La medición se realiza utilizando `time.perf_counter_ns()` para garantizar precisión a nivel de nanosegundos.

### 4.5. Arquitectura de Microservicios

El sistema adopta una arquitectura de microservicios desacoplada, donde cada servicio tiene una responsabilidad única y se comunica con los demás mediante HTTP/REST (JSON). Esta arquitectura permite:

- **Escalabilidad independiente:** Cada servicio puede escalarse según su carga particular.
- **Despliegue independiente:** Los servicios pueden desplegarse y actualizarse de forma independiente.
- **Tolerancia a fallos:** El fallo de un servicio no afecta directamente a los demás.
- **Tecnología heterogénea:** Cada servicio podría implementarse con la tecnología más adecuada.

### 4.6. Normativas de Protección de Datos

| Normativa | Descripción | Relevancia para Enmask |
|---|---|---|
| **GDPR (Art. 32)** | Reglamento General de Protección de Datos de la UE | Requiere medidas técnicas para proteger datos personales |
| **PCI-DSS** | Estándar de Seguridad de Datos de la Industria de Tarjetas de Pago | Requiere enmascaramiento de datos de tarjetas en entornos no productivos |
| **Ley N° 29733 (Perú)** | Ley de Protección de Datos Personales | Establece obligaciones de seguridad para datos personales en Perú |
| **HIPAA** | Ley de Portabilidad y Responsabilidad de Seguros de Salud (EE.UU.) | Requiere protección de información de salud |

---

## 5. DESARROLLO DE LA SOLUCIÓN

### 5.a. Análisis de Factibilidad

#### Factibilidad Técnica

| Aspecto | Evaluación | Justificación |
|---|---|---|
| **Tecnologías maduras** | ✅ VIABLE | Python 3.11+, FastAPI, SQLite, Docker son tecnologías ampliamente adoptadas y documentadas |
| **Drivers de BD disponibles** | ✅ VIABLE | Drivers nativos para los 7 motores: psycopg2, pymysql, pymssql, pymongo, redis, neo4j, cassandra-driver |
| **Cifrado robusto** | ✅ VIABLE | La librería `cryptography` (Fernet) proporciona cifrado AES-128-CBC con autenticación HMAC |
| **Monitoreo del sistema** | ✅ VIABLE | `psutil` permite acceder a métricas de CPU, RAM, disco y uptime de forma multiplataforma |
| **Despliegue containerizado** | ✅ VIABLE | Docker Compose permite orquestar 7+ contenedores con redes y volúmenes persistentes |
| **Compatibilidad cloud** | ✅ VIABLE | Render Blueprint (render.yaml) soporta despliegue de múltiples servicios web |

**Conclusión técnica:** Todas las tecnologías requeridas son maduras, de código abierto y ampliamente adoptadas. No se identifican riesgos técnicos que impidan la implementación.

#### Factibilidad Económica

| Concepto | Costo Estimado | Justificación |
|---|---|---|
| **Licencias de software** | $0 USD | Todas las tecnologías son de código abierto (MIT, GPL, Apache 2.0) |
| **Desarrollo local** | $0 USD | Python, Docker Desktop y VS Code son gratuitos |
| **Despliegue en nube (Render)** | $0-10 USD | Plan Free de Render permite 3 servicios web |
| **Dominio web (opcional)** | $0-12 USD/año | No requerido para el proyecto académico |
| **Total estimado** | **$10 USD** | Costo mínimo para despliegue en nube |

**Conclusión económica:** El costo total del proyecto es mínimo ($10 USD) gracias al uso exclusivo de herramientas gratuitas y créditos educativos. El proyecto es financieramente viable para entornos académicos y organizaciones con presupuesto limitado.

#### Factibilidad Operativa

| Aspecto | Evaluación | Justificación |
|---|---|---|
| **Curva de aprendizaje** | ✅ VIABLE | Python y FastAPI tienen documentación extensa y comunidad activa |
| **Mantenibilidad** | ✅ VIABLE | Arquitectura modular con separación de responsabilidades (SRP) |
| **Extensibilidad** | ✅ VIABLE | Patrón Factory permite agregar nuevos motores sin modificar lógica central |
| **Portabilidad** | ✅ VIABLE | Contenerización Docker garantiza consistencia entre entornos |
| **Documentación** | ✅ VIABLE | Documentación completa en español para usuarios y desarrolladores |

**Conclusión operativa:** El sistema es operable, mantenible y extensible. La arquitectura modular facilita la incorporación de nuevos motores de BD y algoritmos de enmascaramiento.

#### Factibilidad Social

| Aspecto | Evaluación | Justificación |
|---|---|---|
| **Aceptación del usuario** | ✅ VIABLE | Interfaz web intuitiva con Tailwind CSS y dashboard con Chart.js |
| **Necesidad del mercado** | ✅ VIABLE | Alta demanda de herramientas de protección de datos accesibles |
| **Impacto educativo** | ✅ VIABLE | Herramienta valiosa para enseñanza de seguridad de datos |
| **Accesibilidad** | ✅ VIABLE | Interfaz en español, compatible con pantallas >= 1024px |

**Conclusión social:** El proyecto tiene aceptación positiva entre desarrolladores, DBAs, auditores y estudiantes. La disponibilidad como herramienta de código abierto amplía su impacto social.

#### Factibilidad Legal

| Aspecto | Evaluación | Justificación |
|---|---|---|
| **Licencias de software** | ✅ VIABLE | Todas las dependencias usan licencias permisivas (MIT, BSD, Apache 2.0) |
| **Cumplimiento GDPR** | ✅ VIABLE | Implementa cifrado Fernet y gestión segura de claves (Art. 32) |
| **Cumplimiento Ley N° 29733** | ✅ VIABLE | Enmascaramiento y cifrado de datos personales según normativa peruana |
| **Propiedad intelectual** | ✅ VIABLE | Código original del equipo desarrollador |

**Conclusión legal:** El proyecto cumple con las normativas de protección de datos aplicables y utiliza software con licencias sin restricciones.

#### Factibilidad Ambiental

| Aspecto | Evaluación | Justificación |
|---|---|---|
| **Eficiencia energética** | ✅ VIABLE | Procesamiento nativo en motor BD reduce transferencia de datos y consumo de red |
| **Reducción de almacenamiento** | ✅ VIABLE | Enmascaramiento in-place elimina necesidad de copias duplicadas |
| **Huella de carbono** | ✅ VIABLE | Docker optimiza uso de recursos vs. máquinas virtuales tradicionales |

**Conclusión ambiental:** El sistema contribuye a la eficiencia energética al reducir el movimiento de datos y optimizar el procesamiento en el motor de BD.

#### Resumen de Factibilidad

| Dimensión | Resultado | Nivel de Riesgo |
|---|---|---|
| **Técnica** | ✅ VIABLE | Bajo |
| **Económica** | ✅ VIABLE | Muy Bajo |
| **Operativa** | ✅ VIABLE | Bajo |
| **Social** | ✅ VIABLE | Bajo |
| **Legal** | ✅ VIABLE | Muy Bajo |
| **Ambiental** | ✅ VIABLE | Muy Bajo |

**RIESGO GENERAL DEL PROYECTO: MODERADO - CONTROLADO**

Todos los riesgos identificados (técnicos, de seguridad, operativos y de rendimiento) cuentan con estrategias de mitigación concretas documentadas en el FD01.

---

### 5.b. Tecnología de Desarrollo

#### Stack Tecnológico Completo

| Capa | Tecnología | Versión | Propósito |
|---|---|---|---|
| **Backend** | Python | 3.11+ | Lenguaje principal de desarrollo |
| **Framework Web** | FastAPI | Latest | API REST asíncrona de alto rendimiento |
| **Servidor ASGI** | Uvicorn | Latest | Servidor de aplicaciones asíncrono |
| **Frontend** | HTML5 + Tailwind CSS | v4 (CDN) | Interfaz de usuario responsiva |
| **Gráficos** | Chart.js | Latest | Visualización de métricas en tiempo real |
| **Persistencia Interna** | SQLite | Built-in | Almacenamiento de usuarios y métricas |
| **Cifrado** | cryptography (Fernet) | Latest | Cifrado simétrico AES-128-CBC |
| **Hashing** | passlib + bcrypt | 4.0.1 | Hash seguro de contraseñas |
| **HTTP Client** | httpx | Latest | Comunicación entre microservicios |
| **Monitoreo Sistema** | psutil | Latest | Métricas de CPU, RAM, disco |
| **Contenedores** | Docker + Docker Compose | Latest | Containerización y orquestación |
| **Despliegue Cloud** | Render | Free Plan | Hosting en la nube |

#### Drivers de Bases de Datos

| Motor de BD | Driver | Tipo |
|---|---|---|
| PostgreSQL | psycopg2-binary | Relacional (SQL) |
| MySQL | pymysql | Relacional (SQL) |
| SQL Server | pymssql | Relacional (SQL) |
| SQLite | sqlite3 (built-in) | Relacional (SQL) |
| MongoDB | pymongo | Documental (NoSQL) |
| Redis | redis | Clave/Valor (NoSQL) |
| Neo4j | neo4j | Grafos (NoSQL) |
| Cassandra | cassandra-driver | Columnar (NoSQL) |

#### Estructura del Proyecto

```
enmask-v2.0/
├── main.py                    # API Gateway (FastAPI)
├── config.py                  # Configuración centralizada (Pydantic)
├── auth.py                    # Gestión de sesiones y tokens
├── db_usuarios.py             # CRUD de usuarios (SQLite)
├── oauth_google.py            # Google OAuth2
├── database_manager.py        # Factory Pattern (8 motores)
├── database_health.py         # Health checks de BD
├── masking.py                 # Motor de enmascaramiento (4 algoritmos)
├── masking_service.py         # Masking Service (FastAPI :8001)
├── encryption_service.py      # Servicio de cifrado Fernet
├── key_manager.py             # Gestión de clave Fernet
├── governance.py              # Gobernanza SDM
├── monitor_service.py         # Monitor Service (FastAPI :8002)
├── monitor.py                 # Cálculo de overhead
├── health_monitor.py          # Orquestador de salud
├── system_metrics.py          # Métricas de sistema (psutil)
├── service_checker.py         # Health checks HTTP
├── seeder.py                  # Datos de prueba
├── requirements.txt           # Dependencias Python
├── Dockerfile                 # Imagen Docker
├── docker-compose.yml         # Orquestación de contenedores
├── render.yaml                # Blueprint para Render
├── static/
│   ├── login.html             # Página de autenticación
│   └── index.html             # Dashboard principal
└── scripts/
    ├── render-start.sh        # Script de inicio para Render
    └── generate_frontend.py   # Generador de frontend
```

#### Patrones de Diseño Implementados

| Patrón | Ubicación | Propósito |
|---|---|---|
| **Factory Method** | `database_manager.py` | Instanciar el motor de BD correcto según el nombre |
| **Strategy** | `masking.py` | Seleccionar algoritmo de enmascaramiento en runtime |
| **Template Method** | `BaseDeDatos` (abstracta) | Definir contrato común para todos los motores |
| **Singleton** | `config.py` (settings) | Instancia global de configuración |
| **Middleware** | `SessionMiddleware` | Autenticación centralizada en cada request |
| **Proxy** | `main.py` → servicios | API Gateway enruta requests a microservicios |

---

### 5.c. Metodología de Implementación

#### Documento de Visión (FD02)

El Documento de Visión estableció los fundamentos del proyecto:

- **Visión:** Ser una plataforma de referencia en protección de datos sensibles para entornos no productivos.
- **Misión:** Desarrollar una plataforma web que permita proteger información sensible mediante técnicas de enmascaramiento y encriptación estática.
- **Objetivos de negocio:** Automatizar protección de datos, unificar gestión multi-motor, garantizar cumplimiento normativo, medir impacto de seguridad, reducir costos operativos.
- **Alcance:** 7 motores de BD, 4 algoritmos de enmascaramiento, gobernanza SDM, monitoreo de rendimiento, dashboard de observabilidad.

#### Documento SRS (FD03 — Especificación de Requerimientos)

El SRS definió los requerimientos detallados del sistema:

**Requerimientos Funcionales (25 RF):**

| Categoría | Cantidad | Ejemplos principales |
|---|---|---|
| Autenticación | 5 | RF-001 a RF-005 (Registro, Login, OAuth2, Logout, Usuario actual) |
| Conexiones a BD | 4 | RF-006 a RF-009 (Conectar, Listar, Eliminar, Obtener esquema) |
| Enmascaramiento | 4 | RF-010 a RF-014 (Benchmark, Preview, Vista, Cifrar, Descifrar) |
| Gobernanza SDM | 3 | RF-015 a RF-017 (Activar SDM, Restaurar, Estado) |
| Monitoreo | 8 | RF-018 a RF-025 (Sistema, Servicios, BD, Algoritmos, Motor, Métricas, Errores, Health) |

**Requerimientos No Funcionales (20 RNF):**

| Categoría | Cantidad | Ejemplos principales |
|---|---|---|
| Rendimiento | 4 | RNF-001 a RNF-04 (Consultas < 2s, Overhead < 5s, Cifrado < 10s, 10 usuarios) |
| Seguridad | 4 | RNF-005 a RNF-08 (Bcrypt, Fernet, Cookies, Manejo de errores) |
| Disponibilidad | 2 | RNF-009 a RNF-10 (Uptime 95%, Reinicio automático) |
| Arquitectura | 4 | RNF-11 a RNF-14 (Desacoplamiento, Extensibilidad, SRP, Documentación) |
| Usabilidad | 4 | RNF-15 a RNF-18 (Configuración, Español, Responsivo, Auto-refresh) |
| Despliegue | 2 | RNF-19 a RNF-20 (Docker, Render) |

**Reglas de Negocio (15 RN):**

Las reglas de negocio definen las restricciones operativas del sistema, incluyendo validación de credenciales (RN-001), autenticación requerida (RN-002), motores soportados (RN-003), algoritmos válidos (RN-004), medición de tiempos (RN-005), motores SDM (RN-006), backup cifrado obligatorio (RN-007), clave Fernet persistente (RN-008), unicidad de conexiones (RN-009), límite de consultas (RN-010), excepciones registradas (RN-011), seguridad de cookies (RN-012), formato de respuesta (RN-013), comunicación inter-servicio (RN-014) e introspección de esquema (RN-015).

#### Documento SAD (FD04 — Diseño de Arquitectura)

El SAD definió la arquitectura completa del sistema aplicando el modelo de vistas "4+1":

**Vista Lógica:**
- Diagrama de subsistemas (capas: Presentación, API Gateway, Servicios, Datos, Motores)
- Diagrama de clases (BaseDeDatos, DatabaseFactory, MaskingEngine, AuthModule, MonitorService, GovernanceSDM, HealthMonitor)
- Diagrama de objetos (instancias en ejecución)

**Vista de Procesos:**
- Diagrama de procesos del sistema (5 procesos: Autenticación, Conexión, Benchmark/SDM, Almacenamiento, Visualización)
- Diagrama de secuencia (Login, Benchmark)
- Diagrama de actividades con objetos

**Vista de Desarrollo:**
- Diagrama de arquitectura software (estructura de paquetes)
- Diagrama de componentes (microservicios)
- Diagrama de paquetes (capas y módulos)

**Vista Física:**
- Diagrama de despliegue (Docker Compose local + Render cloud)
- Diagrama de base de datos (SQLite interno + motores externos)

**Vista de Casos de Uso:**
- 8 casos de uso documentados (CU-001 a CU-008)
- Trazabilidad CU → Componentes arquitectónicos

---

## 6. CRONOGRAMA

### Cronograma General del Proyecto

| Fase | Actividad | Duración | Semanas |
|---|---|---|---|
| **Fase 1: Planificación** | FD01 — Informe de Factibilidad | 2 semanas | S1-S2 |
| | FD02 — Documento de Visión | 1 semana | S3 |
| **Fase 2: Análisis** | FD03 — Especificación de Requerimientos | 3 semanas | S4-S6 |
| **Fase 3: Diseño** | FD04 — Diseño de Arquitectura | 2 semanas | S7-S8 |
| **Fase 4: Implementación** | FD05 — Implementación y Verificación | 4 semanas | S9-S12 |
| | Configuración del entorno de desarrollo | 2 días | S9 |
| | Desarrollo del API Gateway (main.py) | 3 días | S9-S10 |
| | Desarrollo del Masking Service | 3 días | S10 |
| | Desarrollo del Monitor Service | 3 días | S10-S11 |
| | Desarrollo del Frontend (Dashboard) | 3 días | S11 |
| | Integración y pruebas | 3 días | S11-S12 |
| | Contenerización Docker | 2 días | S12 |
| | Despliegue en Render | 1 día | S12 |
| **Fase 5: Verificación** | Pruebas de integración | 2 días | S12 |
| | Pruebas de rendimiento | 1 día | S12 |
| | Documentación final | 2 días | S12 |
| **Total** | | **12 semanas** | |

### Cronograma de Implementación (Detalle Fase 4)

| Semana | Actividad | Entregable |
|---|---|---|
| **S9** | Configuración entorno, database_manager.py, config.py, auth.py | Módulo de datos y autenticación base |
| **S10** | masking.py, masking_service.py, encryption_service.py, governance.py | Masking Service completo |
| **S11** | monitor_service.py, health_monitor.py, system_metrics.py, frontend | Monitor Service + Dashboard |
| **S12** | Integración, Docker, Render, pruebas, documentación | Sistema completo desplegado |

---

## 7. PRESUPUESTO

### Presupuesto Detallado

| Rubro | Concepto | Costo (USD) | Justificación |
|---|---|---|---|
| **Software** | Python 3.11 | $0 | Software libre (PSF License) |
| | FastAPI | $0 | Software libre (MIT License) |
| | Docker Desktop | $0 | Gratuito para uso educativo |
| | Visual Studio Code | $0 | Software libre (MIT License) |
| | Git | $0 | Software libre (GPL) |
| | Tailwind CSS | $0 | Software libre (MIT License) |
| | Chart.js | $0 | Software libre (MIT License) |
| **Hardware** | Computadora personal | $0 | Ya disponible (8 GB RAM mínimo) |
| **Infraestructura Cloud** | Render (Plan Free) | $0 | 3 servicios web gratuitos |
| | Dominio web (opcional) | $10/año | No requerido para el proyecto |
| **Licencias BD** | PostgreSQL | $0 | Software libre (PostgreSQL License) |
| | MySQL | $0 | Software libre (GPL) |
| | MongoDB | $0 | Software libre (SSPL) |
| | Redis | $0 | Software libre (BSD) |
| | Neo4j Community | $0 | Software libre (GPL) |
| **Capacitación** | Documentación oficial | $0 | Disponible en línea |
| | Tutoriales y cursos | $0 | Recursos gratuitos (YouTube, Docs) |
| **TOTAL** | | **$10 USD** | |

### Comparativa con Soluciones Comerciales

| Solución | Costo Anual | Motor Único | Multi-Motor | Monitoreo |
|---|---|---|---|---|
| **IBM Optim** | $200,000+ | ✅ | ❌ | ❌ |
| **Delphix** | $150,000+ | ✅ | ❌ | ❌ |
| **Informatica** | $100,000+ | ✅ | ❌ | ❌ |
| **Enmask v2.0** | **$10** | ✅ | ✅ (7 motores) | ✅ |

**Ahorro estimado:** 99.99% respecto a soluciones comerciales equivalentes.

---

## 8. CONCLUSIONES

1. **El sistema Enmask v2.0 ha sido implementado exitosamente** como una plataforma de enmascaramiento estático de datos y monitoreo de rendimiento, cumpliendo con todos los requerimientos funcionales y no funcionales especificados en el FD03.

2. **La arquitectura de microservicios desacoplada** (API Gateway + Masking Service + Monitor Service) ha demostrado ser efectiva para separar responsabilidades, permitir el despliegue independiente y facilitar el mantenimiento del sistema.

3. **El patrón Factory para la gestión de motores de BD** permite soportar 7 motores diferentes (PostgreSQL, MySQL, SQL Server, SQLite, MongoDB, Redis, Neo4j) desde una interfaz unificada, cumpliendo con el objetivo de extensibilidad.

4. **Los 4 algoritmos de enmascaramiento** (redacción, hashing, encriptación, FPE simulado) funcionan correctamente en todos los motores soportados, con medición precisa de tiempos mediante `time.perf_counter_ns()`.

5. **El sistema de gobernanza SDM** permite la protección permanente de datos con backup cifrado (Fernet) y restauración completa, garantizando la reversibilidad de las operaciones de enmascaramiento.

6. **El monitor de rendimiento** proporciona métricas cuantitativas del overhead de seguridad, permitiendo a los usuarios tomar decisiones informadas sobre la técnica de enmascaramiento más adecuada según sus requisitos de rendimiento.

7. **El costo total del proyecto ($10 USD)** demuestra que es posible desarrollar herramientas de seguridad de datos robustas y funcionales utilizando exclusivamente tecnologías de código abierto, haciendo el sistema accesible para organizaciones con presupuesto limitado.

8. **La containerización con Docker Compose** garantiza la portabilidad y consistencia del sistema entre entornos de desarrollo, pruebas y producción, cumpliendo con los principios de despliegue moderno.

9. **El cumplimiento normativo** con GDPR (Art. 32), PCI-DSS y Ley N° 29733 se ha logrado mediante la implementación de cifrado robusto (Fernet/AES-128-CBC), gestión segura de claves y auditoría de accesos.

10. **La documentación completa del proyecto** (FD01 a FD05, diagramas UML, código comentado) constituye un valioso recurso académico y profesional para la comprensión y mantenimiento del sistema.

---

## 9. RECOMENDACIONES

1. **Implementar autenticación basada en roles (RBAC)** para diferenciar permisos entre usuarios estándar y administradores, reforzando la seguridad del sistema en entornos productivos.

2. **Agregar soporte para motores de BD adicionales** como Oracle, DB2 y Elasticsearch, aprovechando la extensibilidad del patrón Factory implementado.

3. **Implementar un sistema de alertas por correo electrónico o SMS** para notificar a los administradores sobre eventos críticos (CPU > 80%, servicios DOWN, errores de conexión).

4. **Optimizar el algoritmo FPE simulado** mediante paralelización o reducción de iteraciones, ya que las 5000 iteraciones actuales generan un overhead significativo.

5. **Implementar autenticación LDAP/Active Directory** para integrar el sistema con infraestructuras corporativas existentes.

6. **Agregar soporte para enmascaramiento dinámico (proxy SQL)** que permita proteger datos en tiempo real sin modificar la base de datos original.

7. **Implementar pruebas automatizadas** (unitarias, de integración, de rendimiento) para garantizar la calidad del código y facilitar el mantenimiento continuo.

8. **Desarrollar una CLI (interfaz de línea de comandos)** para permitir la automatización de operaciones de enmascaramiento desde scripts y pipelines de CI/CD.

9. **Implementar un sistema de auditoría completo** que registre todas las operaciones realizadas por los usuarios, incluyendo quién realizó qué operación y cuándo.

10. **Considerar la implementación de FPE estándar (FF1/FF3 de NIST)** para reemplazar el FPE simulado, proporcionando cifrado que preserva formato con respaldo criptográfico formal.

---

## 10. BIBLIOGRAFÍA

1. Kruchten, P. (1995). "The 4+1 View Model of Architecture". *IEEE Software*, 12(6), 42-50.

2. Bass, L., Clements, P., & Kazman, R. (2012). *Software Architecture in Practice* (3rd ed.). Addison-Wesley.

3. Sommerville, I. (2015). *Software Engineering* (10th ed.). Pearson.

4. National Institute of Standards and Technology (NIST). (2016). "Recommendation for Block Cipher Modes of Operation: Methods for Format-Preserving Encryption". NIST SP 800-38G.

5. European Parliament. (2016). "Regulation (EU) 2016/679 — General Data Protection Regulation (GDPR)".

6. Congreso de la República del Perú. (2011). "Ley N° 29733 — Ley de Protección de Datos Personales".

7. Payment Card Industry (PCI). (2022). "PCI Data Security Standard (PCI DSS) v4.0".

8. Fielding, R. T. (2000). "Architectural Styles and the Design of Network-based Software Architectures". Doctoral dissertation, University of California, Irvine.

9. Richardson, C. (2018). *Microservices Patterns*. Manning Publications.

10. FastAPI Documentation. (2024). https://fastapi.tiangolo.com/

11. Python Cryptographic Authority. (2024). "cryptography — Python Cryptographic Authority". https://cryptography.io/

12. Docker Inc. (2024). "Docker Documentation". https://docs.docker.com/

13. Render Inc. (2024). "Render Documentation". https://render.com/docs

---

## 11. ANEXOS

### Anexo 01 — Informe de Factibilidad (FD01)

El Informe de Factibilidad (FD01) evaluó la viabilidad del proyecto Enmask v2.0 en cinco dimensiones:

- **Factibilidad Técnica:** Todas las tecnologías son maduras y de código abierto.
- **Factibilidad Económica:** Costo mínimo ($10 USD) gracias a herramientas gratuitas.
- **Factibilidad Legal:** Cumple con GDPR, PCI-DSS y Ley N° 29733.
- **Factibilidad Social:** Aceptación positiva por desarrolladores, DBAs y auditores.
- **Factibilidad Ambiental:** Reducción de almacenamiento y transferencia de datos.

**Conclusión:** Riesgo general MODERADO - CONTROLADO. Todas las dimensiones son favorables.

*Documento completo disponible en: FD01-Informe-Factibilidad.md*

---

### Anexo 02 — Documento de Visión (FD02)

El Documento de Visión definió los fundamentos conceptuales del proyecto:

- **Visión:** Ser plataforma de referencia en protección de datos para entornos no productivos.
- **Misión:** Desarrollar plataforma web unificada para 7 motores de BD.
- **Objetivos de negocio:** 5 objetivos estratégicos.
- **Objetivos de diseño:** 5 objetivos técnicos.
- **Alcance:** 8 áreas incluidas, 7 áreas excluidas.
- **Perfiles de usuario:** Usuario Estándar y Administrador.

*Documento completo disponible en: FD02-Documento-Vision.md*

---

### Anexo 03 — Documento SRS (FD03)

El Documento de Especificación de Requerimientos (SRS) especificó:

- **25 Requerimientos Funcionales** (RF-001 a RF-025)
- **20 Requerimientos No Funcionales** (RNF-001 a RNF-020)
- **15 Reglas de Negocio** (RN-001 a RN-015)
- **8 Casos de Uso** (CU-001 a CU-008) con narrativa detallada
- **Diagramas UML:** Paquetes, Casos de Uso, Actividades, Secuencia, Clases
- **Análisis de objetos** con atributos, métodos y responsabilidades

*Documento completo disponible en: FD03-Especificacion-Requerimientos.md*

---

### Anexo 04 — Documento SAD (FD04)

El Documento de Diseño de Arquitectura (SAD) definió:

- **Vista Lógica:** Subsistemas, clases, objetos, base de datos
- **Vista de Procesos:** Diagrama de procesos del sistema (5 procesos)
- **Vista de Desarrollo:** Arquitectura software, componentes, paquetes
- **Vista Física:** Despliegue local (Docker) y nube (Render)
- **Vista de Casos de Uso:** Trazabilidad CU → Componentes
- **Atributos de Calidad:** Funcionalidad, Usabilidad, Confiabilidad, Rendimiento, Mantenibilidad

*Documento completo disponible en: FD04-Diseno-Arquitectura.md*

---

### Anexo 05 — Manuales y otros documentos

#### Manual de Usuario

**Requisitos del sistema:**
- Docker Desktop (Windows/macOS) o Docker Engine + Compose Plugin (Linux)
- Al menos 8 GB RAM libres
- Navegador web moderno (Chrome, Firefox, Edge)

**Instalación:**
```bash
# 1. Clonar el repositorio
cd "Multi-DB Masking & Performance Overhead Monitor"

# 2. Crear archivo de entorno
cp .env.example .env

# 3. Editar .env (cambiar SECRET_KEY, ADMIN_PASSWORD)

# 4. Levantar el stack
docker compose up -d --build

# 5. Verificar servicios
docker compose ps
```

**Acceso:**
| Servicio | URL |
|---|---|
| Panel web | http://localhost:8000/login |
| API Gateway | http://localhost:8000 |
| Masking Service | http://localhost:8001 |
| Monitor Service | http://localhost:8002 |

**Credenciales por defecto:**
- Email: `admin@secops.local`
- Contraseña: `Admin1234!`

#### Manual de Desarrollo

**Estructura de módulos:**
- `main.py` — API Gateway con todos los endpoints REST
- `database_manager.py` — Factory Pattern para 7 motores de BD
- `masking.py` — Motor de enmascaramiento con 4 algoritmos
- `masking_service.py` — Microservicio de enmascaramiento (puerto 8001)
- `monitor_service.py` — Microservicio de monitoreo (puerto 8002)
- `auth.py` — Gestión de sesiones y tokens
- `governance.py` — Lógica de gobernanza SDM

**Agregar un nuevo motor de BD:**
1. Crear clase que herede de `BaseDeDatos`
2. Implementar `conectar()`, `obtener_esquema()`, `ejecutar_consulta()`
3. Registrar en `DatabaseFactory.motores`
4. Agregar variables de entorno en `config.py`

**Agregar un nuevo algoritmo de enmascaramiento:**
1. Agregar función en `masking.py`
2. Registrar en el diccionario `ALGORITMOS` de `aplicar_enmascaramiento()`
3. Documentar en `TIPOS_ENMASCARAMIENTO.md`

#### Diagramas UML Completos

Todos los diagramas UML del proyecto están disponibles en sintaxis Mermaid en el archivo:
- `DIAGRAMAS-MERMAID-FD03-FD04.md` (17 diagramas)

Los diagramas incluyen:
1. Diagrama del Proceso Actual (Actividad)
2. Diagrama del Proceso Propuesto (Actividad)
3. Diagrama de Paquetes (Arquitectura)
4. Diagrama de Casos de Uso
5. Diagrama de Actividades — Benchmark (con objetos)
6. Diagrama de Actividades — SDM Protect (con objetos)
7. Diagrama de Secuencia — Login
8. Diagrama de Secuencia — Benchmark
9. Diagrama de Clases
10. Diagrama de Subsistemas (Vista Lógica)
11. Diagrama de Colaboración
12. Diagrama de Objetos
13. Diagrama de Base de Datos (Relacional)
14. Diagrama de Arquitectura Software (Paquetes)
15. Diagrama de Componentes
16. Diagrama de Procesos del Sistema (Actividad)
17. Diagrama de Despliegue (Físico)

---

*Documento generado para el proyecto Enmask v2.0*
*FD05 — Informe de Implementación y Verificación*
*Versión 1.0 — Junio 2026*
*Tacna – Perú*
