# Deployment

## Docker Compose

The project includes a `docker-compose.yml` for containerized deployment.

### Build

```bash
docker-compose build
```

### Run All Services

```bash
docker-compose up -d
```

### Run Specific Services

```bash
# Backend + Frontend only
docker-compose up --build backend frontend

# Training service
docker-compose up --build --profile training model-training
```

### Logs

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop

```bash
docker-compose down
```

## Environment Configuration

### Backend `.env`

Create `.env` in the `backend/` directory:

```env
API_HOST=0.0.0.0
API_PORT=8000
MODEL_PATH=./models
OUTPUT_PATH=./outputs
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Frontend `.env`

Create `.env` in the `frontend/` directory:

```env
VITE_API_URL=http://localhost:8000
```

## Production Considerations

- Use `docker-compose up -d` for detached mode
- Ensure model artifacts are present in `backend/models/` before starting
- Configure `CORS_ALLOWED_ORIGINS` to match your frontend URL
- Set up persistent volumes for model artifacts and output data
- Use HTTPS in production with a reverse proxy

## Scaling

The backend is stateless with respect to prediction logic. For horizontal scaling:

1. Place model files on shared storage
2. Configure a load balancer in front of multiple backend instances
3. Use a shared session store for audit data if needed
