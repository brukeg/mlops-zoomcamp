# MLOps Zoomcamp — Personal Learning Repository

This repo contains my work from the [MLOps Zoomcamp](https://github.com/DataTalksClub/mlops-zoomcamp) 
by DataTalks.Club — a free 9-week course covering the fundamentals of productionizing ML services.

## What This Course Covers

End-to-end MLOps: experiment tracking, pipeline orchestration, model deployment, monitoring, 
and best practices. The running example throughout is predicting NYC taxi ride durations.

## My Setup

Unlike the course default (GitHub Codespaces + Conda), this repo was worked through using:

- **Local:** Mac with pipenv for dependency management
- **Cloud:** AWS (EC2, RDS PostgreSQL, S3, IAM, Secrets Manager) — all in `us-west-2`
- **MLOps stack:** MLflow (systemd on EC2), Mage (Docker on EC2), Docker for all deployments
- **Course materials were adapted** to run against real AWS infrastructure rather than locally

Detailed operational notes, AWS resource IDs, and session runbooks live in [CLAUDE.md](./CLAUDE.md).

---

## Modules

### Module 1 — Introduction (`01-intro/`)

**What it covers:** What MLOps is and why it matters. The MLOps maturity model. Introduction 
to the NYC taxi dataset used throughout the course. Environment setup.

**What I built:** Initial exploration notebook (`lesson-1.3.ipynb`) training a baseline linear 
regression model on NYC green taxi data to predict ride duration.

**Setup used:** GitHub Codespaces + Conda (course default).

---

### Module 2 — Experiment Tracking & Model Management (`02-experiment-tracking/`)

**What it covers:** Why experiment tracking matters. MLflow basics — logging parameters, 
metrics, and artifacts. Model registry — registering models, promoting to Staging/Production, 
loading registered models.

**What I built:** Experiment tracking setup with MLflow backed by RDS PostgreSQL and S3 for 
artifact storage. Ran hyperparameter optimization with XGBoost, logged runs to MLflow, 
registered best models in the Model Registry.

**Infrastructure introduced:** EC2 running MLflow as a systemd service, RDS PostgreSQL as 
backend store, S3 for artifact storage, AWS Secrets Manager for credential management.

---

### Module 3 — Orchestration & ML Pipelines (`03-orchestration/`)

**What it covers:** Workflow orchestration concepts. Building ML pipelines with Mage.

**What I built:** A Mage pipeline (`mlops-pipeline`) with three blocks — data ingestion, 
feature engineering, and XGBoost model training — running on EC2 in Docker. Pipeline logs 
experiments to MLflow automatically on each run.

**Infrastructure introduced:** Mage running in Docker on EC2 using a custom image with 
MLflow and XGBoost pre-installed.

---

### Module 4 — Model Deployment (`04-deployment/`)

**What it covers:** Deployment strategies — online (web service, streaming) vs offline (batch). 
Deploying models as Flask web services. Loading models from MLflow artifact storage.

#### Lesson: `web-service/`

A Flask app serving ride duration predictions, containerized with Docker. Model loaded 
from a local pickle file at image build time.
```bash
# Build and run on EC2
cd 04-deployment/web-service
docker build -t ride-duration-prediction-service:v1 .
docker run -d --name ride-duration -p 9696:9696 ride-duration-prediction-service:v1

# Test
curl -X POST http://localhost:9696/predict \
  -H "Content-Type: application/json" \
  -d '{"PULocationID": 10, "DOLocationID": 50, "trip_distance": 40}'
```

#### Lesson: `web-service-mlflow/`

Upgrades the Flask service to load the model dynamically from S3 via MLflow at container 
startup. Key improvements over the pickle approach:

- No model file baked into the image — model fetched from S3 at startup
- Model version tracked via `RUN_ID` environment variable — explicit and auditable
- DictVectorizer bundled inside the sklearn Pipeline — no separate artifact needed
- IAM role on EC2 handles S3 authentication — no credentials in the container
```bash
# Build and run on EC2
cd 04-deployment/web-service-mlflow
docker build -t ride-duration-prediction-service:mlflow .
docker run -d \
  --name ride-duration-mlflow \
  -p 9696:9696 \
  -e RUN_ID=<mlflow-run-id> \
  -e MLFLOW_TRACKING_URI=http://<ec2-private-ip>:5000 \
  ride-duration-prediction-service:mlflow

# Test
curl -X POST http://localhost:9696/predict \
  -H "Content-Type: application/json" \
  -d '{"PULocationID": 10, "DOLocationID": 50, "trip_distance": 40}'
```

To produce a compatible model artifact, run `random-forest.ipynb` with MLflow tracking 
URI pointed at your MLflow server. The notebook trains a `DictVectorizer + RandomForestRegressor` 
sklearn Pipeline and logs it as a single artifact.

**In progress:** Batch deployment lesson.

