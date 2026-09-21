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

Cross-platform entry-point script (auto-detects OS):

```bash
./scripts/install-dependencies
```

Or using Makefile:

```bash
make install
```

Platform-specific scripts are also available:

```bash
# Linux/macOS
./scripts/install-dependencies.sh

# Windows
scripts\install-dependencies.bat
```

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
source .venv/bin/activate   # Linux
.\.venv\Scripts\activate    # Windows
```

## Verify Installation

```bash
# Check backend
cd backend && python -c "import fastapi; print('FastAPI OK')"

# Check frontend
cd frontend && npx vite --version
```
