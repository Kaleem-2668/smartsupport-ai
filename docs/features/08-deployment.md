# Feature 8: Production Deployment

## Summary

Added production-grade deployment configuration: multi-stage Dockerfiles, production docker-compose with health checks, Nginx reverse proxy with SSL readiness, secure startup scripts with environment validation, and comprehensive architecture documentation.

## Infrastructure Changes

### New Files
- `infra/docker-compose.prod.yml` — Production compose with health checks, persistent volumes, environment variable validation
- `infra/nginx.conf` — Nginx reverse proxy with HTTPS readiness, security headers, CORS, rate limiting
- `infra/startup.sh` — Production startup script with env validation, database backup, log viewing

### Modified Files
- `apps/backend/Dockerfile` — Multi-stage build for production (already existed)
- `apps/frontend/Dockerfile` — Production build stage (already existed)

## Production Architecture

```
                     ┌──────────┐
                     │  Nginx   │  (port 80/443)
                     └────┬─────┘
                  ┌───────┴────────┐
                  ▼                ▼
            ┌──────────┐    ┌──────────┐
            │  Backend  │    │ Frontend │
            │  FastAPI  │    │  Next.js │
            └─────┬─────┘    └──────────┘
          ┌───────┴────────┐
          ▼                ▼
    ┌──────────┐    ┌──────────┐
    │PostgreSQL│    │ ChromaDB │
    └──────────┘    └──────────┘
```

## Deployment Steps

### Prerequisites
- Docker & Docker Compose v2
- OpenAI API key
- Domain name (for HTTPS — optional but recommended)

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | JWT signing key (32+ hex chars: `openssl rand -hex 32`) |
| `POSTGRES_PASSWORD` | ✅ | Database password |
| `AI_API_KEY` | ✅ | OpenAI API key |
| `NEXT_PUBLIC_API_URL` | — | Public API URL (default: backend service URL) |

### Quick Deploy

```bash
# 1. Set required environment variables
export SECRET_KEY="your-32-byte-hex-key"
export POSTGRES_PASSWORD="your-secure-password"
export AI_API_KEY="sk-your-openai-key"

# 2. Deploy
cd infra
docker compose -f docker-compose.prod.yml up --build -d

# 3. Verify
curl http://localhost:8000/api/v1/health
# {"status":"ok"}
```

### Using the Startup Script

```bash
chmod +x infra/startup.sh
./infra/startup.sh prod      # Start production
./infra/startup.sh logs      # View logs
./infra/startup.sh status    # Check service status
./infra/startup.sh backup    # Backup database
./infra/startup.sh validate  # Check environment variables
```

## Security Considerations

### Production Checklist
1. **Generate a strong SECRET_KEY**: `openssl rand -hex 32`
2. **Enable HTTPS**: uncomment SSL lines in nginx.conf and add certificates
3. **Set strong passwords**: change all default passwords
4. **Restrict CORS origins**: update `allow_origins` in backend config
5. **Rate limiting**: configure rate limiting in Nginx or add a middleware
6. **Regular backups**: use `./infra/startup.sh backup` or set up cron

### Environment Validation
The startup script validates all required environment variables before starting services, failing fast with clear error messages if anything is missing.

## Health Checks

All production services have health checks configured:
- **PostgreSQL**: `pg_isready` every 10s
- **ChromaDB**: HTTP health endpoint every 30s
- **Backend**: `GET /api/v1/health` every 30s
- **Nginx**: Monitored by Docker restart policy

Services wait for dependencies to be healthy before starting.
