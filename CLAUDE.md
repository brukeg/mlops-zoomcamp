# MLOps Zoomcamp — Module 4: Model Deployment

## Project Overview
We are working through the MLOps Zoomcamp course. Module 3 (Mage orchestration) is complete.
Module 4 covers model deployment patterns: web service, batch, and streaming.
The web-service lesson deploys a Flask app in Docker serving ride duration predictions.

## AWS Infrastructure

### EC2 Instance
- **Instance ID:** i-048cc37228103a941
- **Type:** m7i-flex.large (2 vCPU, 8GB RAM) — upgraded from t3.small due to OOM issues running MLflow + Mage + XGBoost training concurrently
- **Region:** us-west-2
- **OS:** Amazon Linux
- **SSH:** `ssh -i ~/.ssh/<your-key>.pem ec2-user@<public-dns>`
- Note: Public DNS changes on every stop/start — look it up in EC2 console each session

### EBS Volume
- **Volume ID:** vol-0de90334ed91b6095
- **Size:** 20GB (expanded from 8GB — original was too small for Docker image builds)
- If you ever need to expand again: modify volume in AWS console, then run:
  ```bash
  sudo growpart /dev/nvme0n1 1
  sudo xfs_growfs /
  ```

### RDS (Postgres)
- **Identifier:** mlflow-backend-db
- **Host:** mlflow-backend-db.c1aw8egmm7x1.us-west-2.rds.amazonaws.com
- **Database:** mlflow_db
- **User:** mlflow
- **Password:** stored in AWS Secrets Manager (NOT hardcoded anywhere)
- Stop RDS when not in use to avoid unnecessary cost

### S3
- **Artifact bucket:** mlflow-artifacts-remote-bruke-720881264075-us-west-2-an
- Used by MLflow for model artifact storage

### Secrets Manager
- **Secret name:** mlflow/rds-credentials
- **ARN:** arn:aws:secretsmanager:us-west-2:720881264075:secret:mlflow/rds-credentials-Md9H1c
- Stores RDS username and password as JSON

### IAM
- **Role:** mlflow-ec2-role (attached to EC2 instance)
- **Policy:** mlflow-ec2-policy
  - secretsmanager:GetSecretValue and DescribeSecret on the RDS secret
  - s3:GetObject, PutObject, DeleteObject, ListBucket on the MLflow S3 bucket
- The old `~/.aws/credentials` file (mlflow-user) was renamed to
  `~/.aws/credentials.bak` — instance now authenticates via IAM role only

### Security Group
- Inbound rules open for ports **5000** (MLflow) and **6789** (Mage) from `0.0.0.0/0`
- This is intentional for a dev/course environment — not acceptable for production
- If the rule is scoped to a specific IP and you get "This site can't be reached",
  update the inbound rule to your current IP or re-open to `0.0.0.0/0`

## Services Running on EC2

### MLflow
- **Port:** 5000
- **Managed by:** systemd (`mlflow.service`)
- **Start script:** `/usr/local/bin/start-mlflow.sh`
  - Fetches RDS credentials from Secrets Manager at runtime
  - Constructs connection string in memory — no credentials on disk
- **Commands:**
```bash
  sudo systemctl status mlflow
  sudo systemctl start mlflow
  sudo systemctl stop mlflow
  sudo systemctl restart mlflow
  journalctl -u mlflow -f  # tail logs
```
- **Known issue:** Password is visible in `ps aux` output because it's passed
  as a CLI argument. Fix later using .pgpass or environment variable in systemd unit.

### Mage
- **Port:** 6789
- **Managed by:** Docker with `--restart unless-stopped`
- **Image:** `mageai-custom` (custom image built on EC2 with mlflow and xgboost baked in)
  - Dockerfile is at `/home/ec2-user/Dockerfile`
  - Do NOT use `mageai/mageai:latest` directly — missing required packages
- **Project name:** mlops-pipeline
- **Project location on EC2:** `/home/ec2-user/mlops-pipeline/` (owned by root, managed by Docker)
- **MLFLOW_EC2_HOST:** passed as env var at container startup — must be updated each session
  when EC2 gets a new public DNS
- **Full docker run command** (run this when recreating the container):
```bash
docker run -d \
  --name mage \
  --restart unless-stopped \
  -p 6789:6789 \
  -v /home/ec2-user:/home/src \
  -e MLFLOW_EC2_HOST=<current-public-dns> \
  mageai-custom \
  mage start mlops-pipeline
```
- **Commands:**
```bash
  docker ps                    # check if running
  docker logs mage             # view logs
  docker stop mage             # stop
  docker start mage            # start
  docker restart mage          # restart
```

## Mage Pipeline

### Structure
The pipeline lives in two places:
1. **Git repo (source of truth):** `03-orchestration/mlops-pipeline/`
   - `blocks/ingest_data.py` — data loader block
   - `blocks/prepare_features.py` — feature engineering block
   - `blocks/train_model.py` — XGBoost training + MLflow logging block
   - `pipelines/duration_prediction/metadata.yaml` — pipeline definition
2. **Live Mage project on EC2:** `/home/ec2-user/mlops-pipeline/`
   - Blocks are copied into `data_loaders/` and `transformers/` subdirectories
   - Pipeline definition is at `pipelines/duration_prediction/metadata.yaml`

### Deploying Changes to EC2
When block files are updated locally, deploy to EC2 manually:
```bash
# On EC2 — pull latest from git
cd /home/ec2-user/mlops-zoomcamp && git pull

# Copy blocks to live Mage project
sudo cp 03-orchestration/mlops-pipeline/blocks/ingest_data.py /home/ec2-user/mlops-pipeline/data_loaders/
sudo cp 03-orchestration/mlops-pipeline/blocks/prepare_features.py /home/ec2-user/mlops-pipeline/transformers/
sudo cp 03-orchestration/mlops-pipeline/blocks/train_model.py /home/ec2-user/mlops-pipeline/transformers/
```

### Data Availability Lag
- NYC taxi data on CloudFront lags approximately 6+ months behind the current date
- `get_training_months()` in `duration-prediction.py` will return 403 errors until late 2026
- For testing, hardcode known-good dates in `ingest_data.py`:
  ```python
  df_train = read_dataframe(2021, 1)
  df_val = read_dataframe(2021, 2)
  ```
- Revert to `get_training_months()` once data catches up

### Mage Inter-Block Data Passing
- Mage passes block return values as a flat list to downstream blocks
- Numpy arrays are serialized as dicts — convert to `.tolist()` before returning,
  and back to `np.array()` after unpacking in the next block

## Key Files
- **Pipeline script:** `mlops-zoomcamp/03-orchestration/duration-prediction.py`
- **MLflow start script:** `/usr/local/bin/start-mlflow.sh` (on EC2)
- **MLflow systemd unit:** `/etc/systemd/system/mlflow.service` (on EC2)
- **Mage Dockerfile:** `/home/ec2-user/Dockerfile` (on EC2)

## Known Issues / Deferred Work
1. **RDS password visible in ps aux** — pass via environment variable or .pgpass
   instead of CLI argument in start-mlflow.sh
2. **Mage default password** — change from default admin credentials
3. **MLFLOW_EC2_HOST stale after EC2 restart** — must manually recreate the Mage
   container with updated public DNS each session (see docker run command above)
4. **Block files not version-controlled on EC2** — files in `/home/ec2-user/mlops-pipeline/`
   are owned by root and copied manually from the git repo; consider a proper
   sync script or CI/CD for the capstone
5. **Subsampling in place** — df_train and df_val are sampled to 10,000 rows in ingest_data.py;
   revert if training quality becomes important (e.g. capstone)

## Module 4: Web Service Deployment

### Overview
- Flask app (`predict.py`) serves ride duration predictions on port 9696
- Model loaded from `lin_reg.bin` (pickled DictVectorizer + LinearRegression)
- Containerized with Docker, deployed on EC2
- Port 9696 open in EC2 security group (0.0.0.0/0)

### Files
- `04-deployment/web-service/predict.py` — Flask app
- `04-deployment/web-service/test.py` — test client (points at localhost by default)
- `04-deployment/web-service/Dockerfile` — builds the service image
- `04-deployment/web-service/Pipfile` — pinned deps: scikit-learn==1.0.2, numpy==1.21.6, flask, gunicorn
- `04-deployment/web-service/lin_reg.bin` — pre-trained model (committed to git)

### Running on EC2
```bash
# SSH into EC2, then:
cd /home/ec2-user/mlops-zoomcamp
git pull
cd 04-deployment/web-service
docker build -t ride-duration-prediction-service:v1 .
docker run -d --name ride-duration -p 9696:9696 ride-duration-prediction-service:v1
```

### Testing from Mac
```bash
# Update test.py url to EC2 public DNS, then:
pipenv run python test.py
# Expected: {'duration': 26.43883355119793}
```

### Notes
- numpy must be pinned to 1.21.6 — newer versions cause binary incompatibility with lin_reg.bin
- test.py defaults to localhost; update URL manually when testing against EC2
- Next lesson: web-service-mlflow (loads model from MLflow registry instead of pickle)

## Startup Checklist (Each Session)
1. Start RDS in AWS console, wait for "Available"
2. Start EC2 in AWS console, grab new Public DNS
3. SSH in and verify services:
```bash
   sudo systemctl status mlflow
   docker ps
```
4. If Mage container is stopped (not just restarted), recreate it with updated
   `MLFLOW_EC2_HOST` using the docker run command above
5. If first session after password rotation, update Secrets Manager

## Shutdown Checklist (Each Session)
1. `exit` SSH session
2. Stop EC2 instance in AWS console
3. Stop RDS instance in AWS console
