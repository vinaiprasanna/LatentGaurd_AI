# Contributing Guide

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Run `npm run install` to set up the environment
4. Create a feature branch

## Branch Naming

- `feature/` — New features
- `bugfix/` — Bug fixes
- `docs/` — Documentation changes
- `refactor/` — Code refactoring

## Commit Convention

Use conventional commit messages:

```
feat: add new anomaly detection method
fix: correct data cleaning edge case
docs: update API reference
refactor: simplify risk engine logic
```

## Code Style

- Python: Follow PEP 8 with type hints
- JavaScript/React: Follow the ESLint configuration in the frontend project
- Keep feature modules in `backend/src/` or `model-training/src/`

## Adding New Endpoints

1. Add the route decorator and handler function in `backend/main.py`
2. Define Pydantic models for request/response bodies
3. Add the endpoint to `docs/api-reference.md`
4. Update the architecture diagram in the README

## Adding New Models

1. Implement the model in `backend/src/` or `model-training/src/`
2. Add training script to `model-training/`
3. Update `docs/model-training.md`
4. Export artifacts to `backend/models/`

## Pull Request Process

1. Ensure all tests pass (`python -m pytest tests/ -v`)
2. Update relevant documentation
3. Submit a PR with a clear description of changes
4. Wait for CI/CD checks to pass
5. A maintainer will review and merge

## Reporting Issues

Use the GitHub issue tracker with the appropriate label:
- `bug` — Something is broken
- `enhancement` — Feature request
- `documentation` — Docs improvement
- `question` — Help needed
