# Enmask Roadmap

## v1.0 - Core Masking Engine

**Status: Current**

- Core masking engine with 5 strategies (mask, hash, shuffle, nullify, fake)
- PostgreSQL, MySQL, SQLite support
- Basic RBAC (admin, operator, viewer)
- JWT authentication
- Local Docker deployment
- REST API v1
- Basic PII detection
- Job queue with Celery

## v2.0 - Multi-Database & Advanced Masking

**Status: In Progress**

- 16 database types (Oracle, SQL Server, MongoDB, Redis, Elasticsearch, Cassandra, DynamoDB, Firebase, CockroachDB, TiDB, ClickHouse, Neon, MariaDB, MariaDB, MariaDB)
- 23 masking strategies (tokenize, encrypt, redact, substitute, blur, generalize, date_shift, numeric_noise, partial_mask, reversible, format_preserving, truncate, encode, custom, conditional, cascading, context_aware, deterministic)
- Google OAuth integration
- Column-level encryption
- Reversible masking with key management
- Bulk operations
- API v2 with pagination and filtering
- Connection pooling
- Audit logging

## v3.0 - ML Classification & Compliance

**Status: Planned**

- ML-based PII classification
- Automatic sensitive data discovery
- Compliance reports (GDPR, HIPAA, PCI-DSS, CCPA, SOC2, SOX)
- Data lineage tracking
- Masking templates
- Scheduled jobs
- Webhook notifications
- Multi-tenant support
- SSO (SAML, OIDC)

## v4.0 - Distributed Processing & Real-Time

**Status: Planned**

- Distributed masking with worker nodes
- Real-time streaming masking
- Kafka integration
- Change data capture (CDC)
- Incremental masking
- Cross-database masking
- Custom plugin system
- GraphQL API
- WebSocket events

## v5.0 - Cloud-Native & SaaS

**Status: Planned**

- Kubernetes operator
- Helm charts
- Terraform modules
- AWS/GCP/Azure marketplace
- SaaS multi-tenant offering
- Usage-based billing
- Global edge deployment
- 99.99% SLA
- SOC2 Type II certification

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT
