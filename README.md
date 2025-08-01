# [***PROJECT_NAME***] - Setup Guide

## 🚀 New Project Setup Checklist

### Step 1: Copy and Customize Template
```cmd
REM 1. Copy this template folder to your new project location
xcopy template [***PROJECT_NAME***] /E /I
cd [***PROJECT_NAME***]

REM 2. Find and replace all placeholder text
REM Replace [***PROJECT_NAME***] with your actual project name in:
REM - README.md (4 locations)
REM - frontend/package.json
REM - frontend/index.html  
REM - backend/samconfig.toml (6 locations)
REM - backend/template.yaml
REM - backend/src/template/main.py
REM - backend/src/template/routes/health.py

REM 3. Rename the backend source folder
move backend\src\template backend\src\[***PROJECT_NAME***]
```

### Step 2: Initialize Git and GitHub
```cmd
REM 1. Initialize git repository
git init

REM 2. Create initial commit
git add .
git commit -m "Initial commit: project setup from template"

REM 3. Create GitHub repository (using GitHub CLI)
gh repo create [***PROJECT_NAME***] --private --source=. --remote=origin --push

REM OR manually:
REM - Go to GitHub.com and create new repository
REM - Don't initialize with README (you already have one)
REM - Copy the remote URL and run:
git remote add origin https://github.com/YOUR_USERNAME/[***PROJECT_NAME***].git
git branch -M main
git push -u origin main
```

### Step 3: Set Up Python Virtual Environment
```cmd
REM 1. Navigate to backend directory
cd backend

REM 2. Create virtual environment
python -m venv venv

REM 3. Activate virtual environment (Windows)
venv\Scripts\activate

REM 4. Install Python dependencies
pip install -r src\[***PROJECT_NAME***]\requirements.txt

REM 5. Install development dependencies (optional)
pip install pytest boto3 moto
```

### Step 4: Install Frontend Dependencies
```cmd
REM Navigate to frontend directory
cd ..\frontend

REM Install Node.js dependencies
npm install
```

### Step 5: Create Environment Files
```cmd
REM Backend environment (from backend directory)
copy .env.example .env.local
REM Edit .env.local with your actual values

REM Frontend environment (from frontend directory)  
copy .env.example .env.development
REM Edit .env.development with your API URLs
```

### Step 6: Verify Setup
```cmd
REM Test backend locally (from backend directory with venv activated)
sam local start-api

REM Test frontend (from frontend directory in new terminal)
npm run dev

REM Run tests
npm test
REM or run individually:
REM npm run test:frontend
REM npm run test:backend
```

### Step 7: AWS Setup (when ready to deploy)
```cmd
REM Configure AWS CLI
aws configure

REM Deploy to development environment
npm run deploy:dev
```

---

## Quick Start

### 1. Install Dependencies
```bash
# Use the root package.json for convenience
npm run setup

# Or manually:
# cd frontend && npm install
# cd ../backend && pip install -r src/[***PROJECT_NAME***]/requirements.txt
```

### 2. Development
```bash
# Frontend dev server
npm run dev:frontend

# Backend local API (in separate terminal)
npm run dev:backend

# Or manually:
# cd frontend && npm run dev
# cd backend && sam local start-api
```

### 3. Testing
```bash
# Run all tests
npm test

# Or individually:
npm run test:frontend  # Vue/Vitest tests
npm run test:backend   # Python/pytest tests
```

### 4. Deploy
```bash
# Development environment
npm run deploy:dev

# Production environment  
npm run deploy:prod

# Or manually:
# cd backend && sam deploy --config-env dev|prod
```

## Project Structure
- `package.json` - Root scripts for project management
- `frontend/` - Vue.js 3 + TypeScript application with full tooling
- `backend/` - Python Lambda functions with SAM
- Complete TypeScript, ESLint, and testing configuration
- Environment-based deployment ready

## What's Included
✅ **Frontend Tooling**: TypeScript, ESLint, Vitest, Vite  
✅ **Backend Configuration**: SAM, pytest, environment configs  
✅ **Authentication**: Cognito + JWT middleware ready  
✅ **Database**: DynamoDB tables configured  
✅ **Deployment**: Multi-environment SAM config  
✅ **Development**: Hot reload, local API, testing  

## Next Steps
1. Customize the data models in `backend/src/[***PROJECT_NAME***]/models/`
2. Add your business logic to `backend/src/[***PROJECT_NAME***]/main.py`
3. Create your Vue components in `frontend/src/components/`
4. Update the API service in `frontend/src/services/api.ts`
5. Configure your API URLs in `.env.development` and `.env.production`

This is a complete foundation with all tooling - focus on building your features!
