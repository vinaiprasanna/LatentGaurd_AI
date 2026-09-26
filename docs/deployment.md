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

For direct local backend runs, create `.env` in the `backend/` directory (it is loaded by the API):

```env
API_HOST=0.0.0.0
API_PORT=8000
MODEL_PATH=./models
OUTPUT_PATH=./outputs
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
DATABASE_URL=
```

For Docker Compose, place `DATABASE_URL` and `CORS_ALLOWED_ORIGINS` in a root-level `.env`; Compose passes them to the backend. Do not commit either `.env` file.

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

## Supabase and Hosted Deployment

The API uses Supabase as a standard PostgreSQL database. The database stores prediction job metadata and result snapshots, plus reviewer actions. The Supabase credential is only used by the backend; the Vite frontend must not receive a database password, service-role key, or `DATABASE_URL`.

### 1. Create the database schema

Create a Supabase project, open **SQL Editor**, and run the contents of [`backend/supabase_schema.sql`](../backend/supabase_schema.sql). The API does not run migrations automatically, so create the tables before deploying it.

In **Project Settings → Database**, copy a PostgreSQL connection string. Prefer the Supabase session pooler for a hosted backend, and keep SSL enabled. Set it as `DATABASE_URL` on the backend only. For local development, add it to `backend/.env`; without `DATABASE_URL`, the API continues to use its local JSON/CSV files.

```env
DATABASE_URL=postgresql://...?...&sslmode=require
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://your-app.vercel.app
```

Keep `.env` out of version control and use your host's secret/environment-variable settings in production. Never put the PostgreSQL connection string in a `VITE_` variable.

### 2. Deploy the API to Render

1. Create a Render **Web Service** from the repository and choose **Docker**.
2. Set the root directory to `backend` and the Dockerfile path to `Dockerfile`.
3. Add `DATABASE_URL` and `CORS_ALLOWED_ORIGINS` as environment variables. Set the latter to the frontend origin after creating the Vercel site.
4. Set the health check path to `/health` and deploy.

The trained model files must be available under `backend/models/` in the deployed image for prediction endpoints to work. Confirm that both `anomaly_ensemble_model.pkl` and `drift_model.pkl` are present; the JSON metrics files alone are not model artifacts.

### 3. Deploy the frontend to Vercel

1. Import the same repository into Vercel and set the project root directory to `frontend`.
2. Use `npm run build` as the build command and `dist` as the output directory (Vercel usually detects these for Vite).
3. Set `VITE_API_URL` to the deployed Render API origin, for example `https://your-api.onrender.com`.
4. Redeploy the API with `CORS_ALLOWED_ORIGINS` set to the Vercel site origin, for example `https://your-app.vercel.app`.

After both deploys, verify `https://your-api.onrender.com/health`, then open the Vercel URL and test a CSV prediction. New jobs and review actions will persist across API restarts in Supabase. Existing local JSON/CSV history is not imported automatically.

## Scaling

The backend is stateless with respect to prediction logic. For horizontal scaling:

1. Place model files on shared storage
2. Configure a load balancer in front of multiple backend instances
3. Use a shared session store for audit data if needed
