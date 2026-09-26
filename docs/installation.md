# Installation Guide

## Prerequisites

- Python 3.10+ and pip
- Node.js 18+ and npm
- Git
- Docker and Docker Compose (optional)

## Clone the Repository

```bash
git clone <repository-url>
cd BurnInGuard-AI
```

## Install Dependencies

### Automated (Recommended)

Works on all platforms — Windows, macOS, Linux:

Or use the platform-specific script directly:

```bash
# Linux/macOS
./scripts/install-dependencies.sh

# Windows (CMD)
scripts\install-dependencies.bat

# Windows (PowerShell)
scripts\install-dependencies.ps1
```

The scripts automatically create a Python virtual environment at the project root (`.venv`) and install all Python dependencies. They skip steps that are already done (e.g., if `node_modules` exists, `npm install` is skipped).

### Manual

**Python dependencies:**
```bash
cd backend && pip install -r requirements.txt
cd ../model-training && pip install -r requirements.txt
```

**Node.js dependencies:**
```bash
cd ../frontend && npm install
```

**Root dev dependencies (optional):**
```bash
cd .. && npm install
```

## Virtual Environment

The scripts automatically create a Python virtual environment at the project root (`.venv`). If running manually:

```bash
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
.\.venv\Scripts\activate.bat    # Windows CMD
& .\.venv\Scripts\Activate.ps1  # Windows PowerShell
```

## Verify Installation

```bash
# Check backend
cd backend && python -c "import fastapi; print('FastAPI OK')"

# Check frontend
cd frontend && npx vite --version
```
