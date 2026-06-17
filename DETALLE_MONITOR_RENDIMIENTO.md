# Monitor de Rendimiento e Infraestructura

## ¿Qué hace exactamente?
El monitor de este proyecto ahora mide y almacena tanto el **overhead** de consultas y enmascaramiento como la **salud del sistema**, la **salud de servicios**, el **estado de motores de BD** y los **errores operativos**.

La palabra "infraestructura" ya no se usa solo en sentido descriptivo: el módulo incorpora métricas reales de CPU, memoria, disco, uptime y disponibilidad de servicios para dar una visión de observabilidad más completa.

## Componentes principales

### 1. API Gateway (`main.py`)
- Recibe la petición desde el frontend para consultar una tabla/colección.
- Selecciona el motor de base de datos apropiado usando `DatabaseFactory`.
- Ejecuta el benchmark comparativo y mide:
  - consulta normal
  - consulta enmascarada
  - consulta encriptada
  - comparación histórica por algoritmo
- Envía estas métricas al `Monitor Service`.
- Expone también endpoints de salud para el frontend.

### 2. Masking Service (`masking_service.py` / `masking.py`)
- Recibe los resultados de la consulta y las reglas de enmascaramiento.
- Aplica enmascaramiento académico no destructivo para visualización.
- Expone vista previa, vista académica, cifrado y desencriptación.
- Retorna métricas por algoritmo para alimentar el ranking histórico.

### 3. Monitor Service (`monitor_service.py`)
- Expone endpoints para:
  - métricas históricas de rendimiento (`/metrics`)
  - métricas de sistema (`/system/metrics`)
  - salud de servicios (`/service-health`)
  - salud de bases de datos (`/db-health`)
  - ranking de algoritmos (`/algorithm-ranking`)
  - estadísticas por motor (`/engine-stats`)
  - registro de errores (`/errors`)
- Utiliza SQLite local (`monitor_metrics.db`) para persistir todos los registros.

## Flujo detallado de monitoreo

1. El frontend pide datos desde la API principal.
2. La API ejecuta la consulta contra el motor de BD elegido.
3. Se mide el tiempo de consulta cruda: `tiempo_bd_ms`.
4. Si hay reglas de enmascaramiento:
   - la API envía los datos al `Masking Service`.
   - el servicio enmascara y devuelve los datos procesados.
   - se recibe `tiempo_mask_ms`.
5. La API calcula `overhead_total_ms = tiempo_bd_ms + tiempo_mask_ms`.
6. La API envía un payload al `Monitor Service` para registrar la métrica.
7. El `Monitor Service` guarda el registro en SQLite.
8. El frontend puede luego consultar las métricas almacenadas para mostrar gráficas o histórico.

## Métricas que guarda el monitor

- `motor_utilizado`: nombre del motor de base de datos consultado.
- `tiempo_bd_ms`: duración de la consulta cruda contra la base de datos.
- `tiempo_mask_ms`: duración del proceso de enmascaramiento.
- `overhead_total_ms`: suma de los dos tiempos anteriores.
- `filas_procesadas`: cantidad de filas devueltas y procesadas.
- `timestamp`: marca de tiempo UTC de la métrica.
- `masking_mode`: modo de enmascaramiento o cifrado evaluado.
- `tiempo_normal_ms`, `tiempo_masked_ms`, `tiempo_encrypted_ms`: comparación de rendimiento.
- `latency_delta_ms`: diferencia entre la consulta normal y las variantes protegidas.
- `cpu_overhead`: sobrecosto acumulado de la capa de protección.

## Archivos clave

- `main.py`: flujo de ejecución, medición de tiempos y envío de métricas.
- `monitor.py`: módulo auxiliar que define una función `monitor_overhead(...)` para calcular el overhead localmente.
- `monitor_service.py`: servicio de almacenamiento de métricas con SQLite.

## Cómo se almacena el historial

El `Monitor Service` persiste las métricas en una tabla `metrics` de SQLite:
- `id`
- `motor_utilizado`
- `masking_mode`
- `tiempo_normal_ms`
- `tiempo_masked_ms`
- `tiempo_encrypted_ms`
- `latency_delta_ms`
- `cpu_overhead`
- `tiempo_bd_ms`
- `tiempo_mask_ms`
- `overhead_total_ms`
- `filas_procesadas`
- `timestamp`

Además conserva tablas específicas para:
- `system_metrics`
- `db_health`
- `service_health`
- `algorithm_metrics`
- `system_errors`

Esto permite consultar el histórico y analizar cómo cambian los tiempos según el motor de BD y las reglas de enmascaramiento.

## Limitaciones actuales

- El alcance sigue centrado en la observabilidad de la aplicación y el stack de servicios, no en telemetría de red de bajo nivel.
- El monitoreo de red entre servicios se limita al tiempo de respuesta de health checks HTTP.
- La visibilidad depende de que existan conexiones activas para evaluar motores de BD.

## Conclusión

El monitor de rendimiento e infraestructura del proyecto hace lo siguiente:
- cuantifica el tiempo de consulta a la base de datos,
- cuantifica el tiempo de enmascaramiento de datos,
- suma ambos para obtener el overhead total,
- guarda esos datos para análisis histórico,
- y permite comparar el impacto de aplicar seguridad sobre distintos motores de BD.

En resumen, el monitor mide **el costo de performance que agrega la capa de seguridad al procesamiento de datos**.

## Expansión de observabilidad

La versión ampliada también permite:
- ver recursos del sistema como CPU, RAM, disco y uptime,
- verificar disponibilidad de API, masking service y monitor service,
- comprobar la salud de motores PostgreSQL, MySQL, SQL Server, SQLite, MongoDB, Redis y Neo4j,
- registrar errores operativos,
- comparar algoritmos de enmascaramiento,
- y agrupar estadísticas por motor para el dashboard multi-DB.
