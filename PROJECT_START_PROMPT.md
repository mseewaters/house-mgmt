**I'm starting a new Vue.js + FastAPI + AWS SAM project called `house-mgmt`. Please use my template at `C:\Users\see_w\dev\Projects\template` as the foundation.**
## Key Requirements

**Architecture & Best Practices:**
- Use the exact file structure from the template
- Follow all CORS guidelines (choose API Gateway OR FastAPI, never both)
- Implement structured JSON logging with correlation IDs
- Use absolute imports only (`from app.module import x`)
- Store all timestamps in UTC, convert for display only
- Validate ALL inputs with Pydantic models

**Security Requirements:**
- No secrets in code or git history
- Use environment variables and AWS Secrets Manager
- Implement proper JWT authentication with expiration
- Add rate limiting to sensitive endpoints
- Generic error messages for users, detailed logs for developers

**Code Quality:**
- Type hints and docstrings for all functions
- Paired tests for every feature (pytest for backend, vitest for frontend)
- Separation of concerns with proper layering
- Mock AWS resources in tests

**Development Process:**
- Create working thin vertical slices
- Test locally with `sam local` + Vue dev server before deploying
- Run lint, type-check, and tests before commits
- Use structured logging throughout
---

**Remember**: You are my senior software engineering pair programmer. Use the template's best practices as gospel, and help me build this project the right way from day one.