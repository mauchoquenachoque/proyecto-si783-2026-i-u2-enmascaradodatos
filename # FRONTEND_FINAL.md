# FRONTEND_FINAL.md

## Objetivo

Transformar el frontend actual en un dashboard profesional de observabilidad y seguridad inspirado en Grafana, Datadog y Zabbix, aprovechando todas las métricas ya disponibles en el backend.

- **NO** modificar la lógica existente.
- **NO** romper endpoints actuales.
- **SOLO** expandir visualización, experiencia de usuario y monitoreo.

---

## Estructura General del Dashboard

Dividir la interfaz en 4 módulos principales:

1. **Security Dashboard**
2. **Health Monitor Dashboard**
3. **Database Observatory**
4. **Algorithm Analytics**

---

## MÓDULO 1 – Security Dashboard

Crear una sección dedicada al enmascaramiento y encriptación.

### Panel de Configuración

Agregar controles visuales:

#### Activar/Desactivar columnas (Checkboxes)

- ☑ Nombre
- ☑ DNI
- ☑ Email
- ☑ Teléfono
- ☑ Dirección

#### Selección de algoritmo (Dropdown)

- Redacción
- Hashing
- Encriptación
- FPE

#### Botones

- Aplicar Enmascaramiento
- Restaurar Vista
- Encriptar Datos
- Desencriptar Datos

---

### Vista Comparativa

Mostrar dos tablas simultáneamente.

| Tabla Original       | Tabla Enmascarada     |
|----------------------|-----------------------|
| Nombre     | DNI     | Nombre       | DNI       |
| Eduardo Flores | 12345678 | E** F***     | 123****8  |

---

### Panel de Encriptación

Mostrar:

- **Antes:** `12345678`
- **Después:** `gAAAAAB....`
- **Indicador:** Encriptado / Desencriptado

---

### Flujo Académico

Agregar una visualización tipo pipeline:

Datos Originales
|
Algoritmo
|
Resultado

---

## MÓDULO 2 – Health Monitor Dashboard

### Gráficos Temporales (utilizando Chart.js)

- **CPU Histórico** – Línea temporal
- **RAM Histórica** – Línea temporal
- **Disco Histórico** – Línea temporal

---

## MÓDULO 3 – Database Observatory

Crear sección especializada para motores de bases de datos.

### Estado de Motores

| Motor      | Estado | Latencia |
|------------|--------|----------|
| PostgreSQL | UP     | 12 ms    |
| MySQL      | UP     | 10 ms    |
| SQL Server | UP     | 18 ms    |
| MongoDB    | UP     | 8 ms     |
| Redis      | UP     | 3 ms     |
| Neo4j      | UP     | 9 ms     |

### Indicadores Visuales

- **UP** → verde
- **DOWN** → rojo

### Ranking de Rendimiento

Gráfico de barras comparando:

- PostgreSQL
- MySQL
- SQL Server
- MongoDB
- Redis
- Neo4j

**Métrica:** latencia promedio.

### Disponibilidad

Mostrar:

- Servicios Activos
- Bases Activas
- Errores Detectados

---

## MÓDULO 4 – Algorithm Analytics

Crear dashboard académico.

### Comparación de Algoritmos

| Algoritmo     | Tiempo Promedio |
|---------------|-----------------|
| Redacción     | 1 ms            |
| Hashing       | 4 ms            |
| Encriptación  | 8 ms            |
| FPE           | 15 ms           |

### Gráfico de Overhead (Chart.js – barras)

Comparar:

- Consulta Cruda
- Consulta + Redacción
- Consulta + Hashing
- Consulta + Encriptación
- Consulta + FPE

### Métricas de Impacto

Mostrar:

- Tiempo BD
- Tiempo Mask
- Overhead
- Filas Procesadas

---

## Panel de Alertas

Crear nueva tarjeta con alertas:

- **Alertas CPU** → Si CPU > 80% → mostrar **CPU ALTA**
- **Alertas RAM** → Si RAM > 85% → mostrar **MEMORIA ALTA**
- **Alertas Disco** → Si Disco > 90% → mostrar **DISCO CRÍTICO**
- **Alertas Servicios** → Si un servicio responde DOWN → mostrar **SERVICIO NO DISPONIBLE**
- **Alertas Bases de Datos** → Si una base falla → mostrar alerta correspondiente

---

## Navegación

Agregar menú lateral con las siguientes secciones:

- Dashboard General
- Security Dashboard
- Health Monitor
- Database Observatory
- Algorithm Analytics
- Logs
- Configuración

---

## Dashboard General

Vista ejecutiva que muestre:

- Servicios Activos
- Bases Activas
- CPU
- RAM
- Disco
- Uptime
- Consultas Ejecutadas
- Overhead Promedio

---

## Sistema de Actualización

Refrescar métricas automáticamente:

- **Intervalo:** 5 segundos
- Sin recargar página
- Utilizar `fetch()` o `axios`

---

## Experiencia Visual

- Usar **Tailwind CSS**
- Diseño **oscuro**
- Tarjetas modernas
- Sombras suaves
- Gráficos responsivos
- Badges de estado
- Indicadores visuales grandes

---

## Resultado Esperado

El frontend debe parecer una plataforma profesional de observabilidad y seguridad que combine:

- Data Masking
- Encryption
- Health Monitoring
- Infrastructure Monitoring
- Database Monitoring
- Performance Analytics

en una única interfaz integrada.

La interfaz debe permitir demostrar visualmente:

1. Datos originales.
2. Datos enmascarados.
3. Datos encriptados.
4. Impacto del enmascaramiento.
5. Estado de la infraestructura.
6. Estado de los motores de bases de datos.
7. Salud de los servicios.
8. Consumo de recursos.
9. Alertas.
10. Métricas históricas.
