<div align="center">

# Enmask

**Enterprise Data Masking Platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0.0-green.svg)](CHANGELOG.md)
[![API](https://img.shields.io/badge/API-v2-orange.svg)](docs/api)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue.svg)](tsconfig.json)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](backend/requirements.txt)

[Documentation](docs/) | [API Reference](docs/api/) | [SDKs](sdk/) | [Roadmap](ROADMAP.md)

</div>

---

## What is Enmask?

Enmask is an enterprise-grade data masking platform that protects sensitive data across 16 database types with 23 masking strategies. It enables organizations to comply with GDPR, HIPAA, PCI-DSS, CCPA, SOC2, and SOX while maintaining data utility for development, testing, and analytics.

## Why Enmask?

- **Compliance**: Meet regulatory requirements with built-in compliance reports
- **Security**: Protect PII, PHI, and financial data with cryptographic masking
- **Scale**: Process millions of records with distributed job queues
- **Flexibility**: 23 masking strategies for any use case
- **Multi-DB**: Support for 16 database types out of the box

---

## Features

### Masking Strategies (23)

| Strategy | Description | Reversible |
|----------|-------------|------------|
| `mask` | Replace characters with mask symbols | No |
| `hash` | SHA-256 hash | No |
| `tokenize` | Replace with tokens | Yes |
| `encrypt` | AES-256 encryption | Yes |
| `redact` | Remove entirely | No |
| `shuffle` | Random row shuffling | No |
| `nullify` | Replace with NULL | No |
| `substitute` | Replace with realistic fake data | No |
| `blur` | Reduce precision | No |
| `generalize` | Broaden categories | No |
| `date_shift` | Shift dates by random offset | Yes |
| `numeric_noise` | Add random noise to numbers | No |
| `fake` | Generate realistic fake values | No |
| `partial_mask` | Mask portion of value | No |
| `reversible` | Two-way masking | Yes |
| `format_preserving` | Maintain format | Yes |
| `truncate` | Truncate to length | No |
| `encode` | Base64 encoding | Yes |
| `custom` | User-defined function | Varies |
| `conditional` | Apply based on conditions | Varies |
| `cascading` | Chain multiple strategies | Varies |
| `context_aware` | Context-sensitive masking | Varies |
| `deterministic` | Same input = same output | No |

### Supported Databases (16)

| Database | Versions |
|----------|----------|
| PostgreSQL | 12+ |
| MySQL | 8+ |
| MongoDB | 5+ |
| SQLite | 3+ |
| Oracle | 19c+ |
| SQL Server | 2019+ |
| MariaDB | 10.5+ |
| Redis | 6+ |
| Elasticsearch | 7+ |
| Cassandra | 4+ |
| DynamoDB | Latest |
| Firebase | Latest |
| CockroachDB | 22+ |
| TiDB | 6+ |
| ClickHouse | 22+ |
| Neon | Latest |

### Additional Features

- **RBAC**: Admin, Operator, Viewer roles with granular permissions
- **PII Detection**: Automatic scanning for sensitive columns
- **Job Queue**: Async processing with Celery and Redis
- **Audit Logging**: Complete activity tracking
- **API Versioning**: v1 (legacy) and v2 (current)
- **Plugin System**: Extend with custom masking strategies
- **SDKs**: Official Python and TypeScript clients

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer                            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                     API Gateway (FastAPI)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Auth    │  │  Rules   │  │  Jobs    │  │ Reports  │        │
│  │  Module  │  │  Module  │  │  Module  │  │  Module  │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │              │              │              │              │
│  ┌────▼──────────────▼──────────────▼──────────────▼────┐       │
│  │              Core Masking Engine                      │       │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │       │
│  │  │ Strategy│  │ Strategy│  │ Strategy│  │ Strategy│ │       │
│  │  │  Mask   │  │  Hash   │  │ Encrypt │  │  Fake   │ │       │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │       │
│  └──────────────────────────────────────────────────────┘       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼───────┐  ┌────────────▼──────────┐  ┌────────▼────────┐
│   PostgreSQL  │  │      Redis            │  │    Celery       │
│   (Metadata)  │  │   (Cache/Queue)       │  │   (Workers)     │
└───────────────┘  └───────────────────────┘  └─────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼───────┐  ┌────────────▼──────────┐  ┌────────▼────────┐
│   Target DB   │  │     Target DB         │  │   Target DB     │
│  (PostgreSQL) │  │      (MongoDB)        │  │    (MySQL)      │
└───────────────┘  └───────────────────────┘  └─────────────────┘
```

---

## Quick Start

### Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/enmask/enmask-platform.git
cd enmask-platform

# Create environment file
cp .env.example .env

# Start all services
docker compose up -d

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 3000 | React UI |
| `backend` | 8000 | FastAPI API |
| `postgres` | 5432 | Metadata database |
| `redis` | 6379 | Cache and queue |
| `celery` | - | Background workers |

---

## Local Development

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest --cov=app tests/

# Frontend tests
cd frontend
npm test
```

---

## Environment Variables

### Backend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `REDIS_URL` | Yes | - | Redis connection string |
| `SECRET_KEY` | Yes | - | JWT signing key |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm |
| `JWT_EXPIRATION` | No | `3600` | Token expiration (seconds) |
| `GOOGLE_CLIENT_ID` | No | - | Google OAuth client ID |
| `CORS_ORIGINS` | No | `*` | Allowed CORS origins |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `SENTRY_DSN` | No | - | Sentry error tracking |
| `MAX_CONNECTIONS` | No | `100` | DB connection pool size |
| `WORKER_CONCURRENCY` | No | `4` | Celery worker threads |

### Frontend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | Yes | - | Backend API URL |
| `VITE_GOOGLE_CLIENT_ID` | No | - | Google OAuth client ID |
| `VITE_SENTRY_DSN` | No | - | Sentry DSN |

---

## API Documentation

### v2 (Current)

Base URL: `/api/v2`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Email/password login |
| `/auth/google` | POST | Google OAuth login |
| `/connections` | GET | List connections |
| `/connections` | POST | Create connection |
| `/connections/{id}` | DELETE | Delete connection |
| `/connections/{id}/test` | POST | Test connection |
| `/connections/{id}/discover` | POST | Discover PII |
| `/rules` | GET | List masking rules |
| `/rules` | POST | Create rule |
| `/rules/{id}` | PUT | Update rule |
| `/rules/{id}` | DELETE | Delete rule |
| `/jobs` | GET | List jobs |
| `/jobs` | POST | Create job |
| `/jobs/{id}/run` | POST | Run job |
| `/jobs/{id}/unmask` | POST | Unmask job |
| `/jobs/{id}/share` | POST | Share job |
| `/reports/summary` | GET | Summary report |
| `/reports/compliance/{framework}` | GET | Compliance report |
| `/discovery/scan` | POST | Start PII scan |
| `/discovery/scans/{id}` | GET | Scan results |

Full API docs available at `/docs` (Swagger) and `/redoc` (ReDoc).

### v1 (Legacy)

Base URL: `/api/v1`

See [v1 Documentation](docs/api/v1.md) for details.

---

## Security

### Authentication

- JWT-based authentication
- Google OAuth 2.0
- API key authentication for programmatic access
- Token refresh mechanism

### Authorization

- Role-Based Access Control (RBAC)
- Three default roles: Admin, Operator, Viewer
- Granular permissions per resource
- Resource-level access control

### Data Security

- All passwords hashed with bcrypt
- Encryption at rest for sensitive configurations
- TLS 1.3 for all connections
- No plaintext credentials stored
- Audit logging for all operations

---

## Compliance Frameworks

| Framework | Status | Report |
|-----------|--------|--------|
| GDPR | Supported | Yes |
| HIPAA | Supported | Yes |
| PCI-DSS | Supported | Yes |
| CCPA | Supported | Yes |
| SOC2 | Supported | Yes |
| SOX | Supported | Yes |
| ISO 27001 | Partial | No |
| NIST | Partial | No |

Generate compliance reports via API or UI.

---

## Plugin System

Extend Enmask with custom masking strategies:

```python
# backend/plugins/custom_strategy.py
from app.masking.base import BaseStrategy

class CustomStrategy(BaseStrategy):
    name = "custom_anonymize"
    
    def mask(self, value: str, params: dict) -> str:
        # Your custom logic
        return anonymized_value
```

Register in configuration:

```yaml
plugins:
  - name: custom_anonymize
    module: plugins.custom_strategy
    class: CustomStrategy
```

---

## SDK Usage

### Python

```bash
pip install enmask-sdk
```

```python
from enmask import EnmaskClient

with EnmaskClient("https://api.enmask.io", api_key="your-key") as client:
    # List connections
    connections = client.list_connections()
    
    # Create masking rule
    rule = client.create_rule({
        "name": "Mask Emails",
        "strategy": "partial_mask",
        "target_columns": ["email"],
        "parameters": {"mask_char": "*", "visible_chars": 3}
    })
    
    # Run masking job
    job = client.create_job({
        "name": "Production Masking",
        "connection_id": connections[0].id,
        "rule_ids": [rule.id]
    })
    client.run_job(job.id)
```

### TypeScript

```bash
npm install @enmask/sdk
```

```typescript
import { EnmaskClient, MaskingStrategy } from "@enmask/sdk";

const client = new EnmaskClient("https://api.enmask.io", "your-key");

// List connections
const connections = await client.listConnections();

// Create masking rule
const rule = await client.createRule({
  name: "Mask Emails",
  strategy: MaskingStrategy.PARTIAL_MASK,
  target_columns: ["email"],
  parameters: { mask_char: "*", visible_chars: 3 }
});

// Run masking job
const job = await client.createJob({
  name: "Production Masking",
  connection_id: connections[0].id,
  rule_ids: [rule.id]
});
await client.runJob(job.id);
```

---

## Deployment

### Docker

```bash
docker build -t enmask-backend ./backend
docker build -t enmask-frontend ./frontend

docker run -d -p 8000:8000 enmask-backend
docker run -d -p 3000:3000 enmask-frontend
```

### Kubernetes

```bash
# Using Helm
helm repo add enmask https://charts.enmask.io
helm install enmask enmask/enmask-platform

# Using kubectl
kubectl apply -f k8s/
```

### Production Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Configure TLS certificates
- [ ] Set up database backups
- [ ] Configure monitoring (Prometheus/Grafana)
- [ ] Set up error tracking (Sentry)
- [ ] Configure log aggregation
- [ ] Set resource limits
- [ ] Enable rate limiting
- [ ] Review CORS settings
- [ ] Set up health checks

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow existing code style
- Add tests for new features
- Update documentation
- Ensure all checks pass

---

## Troubleshooting

### Common Issues

**Connection refused**
```bash
# Check if services are running
docker compose ps

# Check logs
docker compose logs backend
```

**Migration errors**
```bash
# Reset database
alembic downgrade base
alembic upgrade head
```

**Redis connection failed**
```bash
# Verify Redis is running
redis-cli ping
```

**Permission denied**
```bash
# Check user role
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v2/auth/me
```

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for detailed release plans.

- **v1.0** - Core masking, 3 DB types
- **v2.0** - Multi-DB (16 types), advanced masking
- **v3.0** - ML classification, compliance reports
- **v4.0** - Distributed processing, real-time masking
- **v5.0** - Cloud-native, SaaS offering

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [React](https://react.dev/) - UI library
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [Celery](https://docs.celeryq.dev/) - Task queue
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Faker](https://faker.readthedocs.io/) - Data generation

---

<div align="center">

**[Documentation](docs/)** | **[API Reference](docs/api/)** | **[SDKs](sdk/)** | **[Roadmap](ROADMAP.md)**

Made with care by the Enmask Team

</div>
