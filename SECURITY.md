# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please:

1. **Do not** open a public issue — use private disclosure
2. Email the maintainers at security@smartsupport.ai
3. Include a description of the vulnerability and steps to reproduce

We will acknowledge receipt within 48 hours and work on a fix promptly.

## Security Measures

### Authentication
- JWT access tokens (15 min expiry) with refresh token rotation
- bcrypt password hashing (12 rounds)
- Token type validation (access vs refresh tokens are distinct)

### Data Isolation
- All resources scoped to user ID
- Cross-user access returns 403/404 consistently
- Document embeddings stored per-user or per-knowledge-base collection

### File Upload
- MIME type whitelist (PDF, TXT, MD, DOC, DOCX only)
- File size limit: 10MB
- Path traversal prevention via UUID filenames

### API
- CORS restricted to configured origins
- Input validation via Pydantic schemas
- Domain exceptions map to appropriate HTTP status codes

## Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `SECRET_KEY` | JWT signing key | Yes (32+ hex chars) |
| `AI_API_KEY` | OpenAI API key | Yes |
| `POSTGRES_PASSWORD` | Database password | Yes |

Never commit `.env` files. Use `.env.example` as a template.
