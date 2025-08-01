# New Project Start Prompt

Copy and paste this prompt when starting a new project with Claude Code:

---

**I'm starting a new Vue.js + FastAPI + AWS SAM project called `[PROJECT_NAME]`. Please use my template at `C:\Users\see_w\dev\Projects\template` as the foundation.**

## Setup Instructions

1. **Read and fully digest** my `Best-practices.md` file and `/examples/` folder
2. **Copy the template** to a new project directory named `[PROJECT_NAME]`
3. **Follow the development workflow** outlined in the best practices:
   - Ask 3 clarifying questions about edge cases, data models, UX, and infrastructure
   - Propose an implementation plan before coding
   - Generate code with proper separation of concerns (API → Service → DAL)

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

## Project Context
[Describe your specific project requirements here - what you're building, key features, target users, etc.]

## Questions to Address
Please ask me 3 clarifying questions about:
1. Edge cases and error scenarios for this specific project
2. Data models and validation rules needed
3. UX/UI behavior and states
4. Infrastructure and deployment requirements

After I answer, propose a detailed implementation plan following the template's architecture and best practices.

---

**Remember**: You are my senior software engineering pair programmer. Use the template's best practices as gospel, and help me build this project the right way from day one.