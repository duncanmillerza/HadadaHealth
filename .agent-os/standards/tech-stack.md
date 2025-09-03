# Tech Stack

## Context

Global tech stack defaults for Agent OS projects, overridable in project-specific `.agent-os/product/tech-stack.md`.

- App Framework: FastAPI 0.112+
- Language: Python 3.12+
- ASGI Server: Uvicorn with standard extras
- Primary Database: PostgreSQL 17+ (SQLite for development)
- ORM/Database: SQLite3 direct queries (migration to SQLAlchemy planned)
- API Documentation: FastAPI automatic OpenAPI/Swagger
- Data Validation: Pydantic 2.9+
- Template Engine: Jinja2 3.1+
- Authentication: Session-based with bcrypt password hashing
- Environment Management: python-dotenv for configuration
- HTTP Client: httpx for external API calls
- JavaScript Framework: Vanilla JavaScript (React migration planned)
- Build Tool: Native browser modules (Vite migration planned)
- Package Manager: pip with requirements.txt
- Python Version: 3.12+
- CSS Framework: Vanilla CSS (TailwindCSS migration planned)
- UI Components: Custom HTML components
- Font Provider: Google Fonts
- Font Loading: Self-hosted for performance
- Icons: Custom SVG icons (Lucide migration planned)
- File Handling: python-multipart + aiofiles
- PDF Generation: ReportLab 4.2+
- Data Processing: pandas 2.2+ + numpy 2.1+
- Application Hosting: Render (Digital Ocean migration planned)
- Hosting Region: Primary region based on user base
- Database Hosting: Render PostgreSQL (managed service)
- Database Backups: Daily automated
- Asset Storage: Local filesystem (S3 migration planned)
- CDN: Native hosting (CloudFront migration planned)
- Asset Access: Direct serving with authentication
- CI/CD Platform: GitHub Actions
- CI/CD Trigger: Push to main/staging branches
- Tests: pytest (implementation planned)
- Production Environment: main branch
- Staging Environment: staging branch
- Security: Environment variables, SQL injection protection, session security
  - Compliance: POPIA/GDPR automation + audit logging
  - Medical Standards: HL7 FHIR + ICD-10 codes
