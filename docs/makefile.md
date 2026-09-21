# Makefile Reference

The project includes a `Makefile` at the root for cross-platform command execution. It works on Linux, macOS, and Windows (with GNU Make installed).

## Prerequisites

- GNU Make (or `make` available in your PATH)
- On Windows: install [Make for Windows](https://www.gnu.org/software/make/) or use Git Bash

## Available Targets

| Target | Description |
|--------|-------------|
| `make install` | Install all dependencies (frontend, backend, model-training) |
| `make dev` | Start backend and frontend concurrently |
| `make dev-backend` | Start backend only on port 8000 |
| `make dev-frontend` | Start frontend dev server on port 3000 |
| `make train` | Train all ML models (anomaly ensemble + drift) |
| `make build` | Build all Docker images |
| `make up` | Start all services via Docker Compose |
| `make down` | Stop all Docker services |
| `make logs` | Stream backend Docker logs |
| `make test` | Run backend and frontend tests |
| `make clean` | Remove generated artifacts (outputs, models, dist) |
| `make all` | Alias for `make dev` (default) |

## Usage Examples

```bash
# Install dependencies
make install

# Start development environment
make dev

# Train models
make train

# Build and deploy with Docker
make build && make up

# Run tests
make test

# Clean up
make clean
```

## Cross-Platform Notes

- On **Linux/macOS**: `make` commands work natively
- On **Windows**: Use Git Bash or WSL to run `make`
- The Makefile delegates to the `scripts/` entry-point scripts, which auto-detect the OS and call the appropriate platform-specific variant (`.sh` or `.bat`)

## Custom Targets

You can add custom targets by editing `Makefile`. All targets are defined as `.PHONY` and can be extended.
