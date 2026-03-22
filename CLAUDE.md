# MLOps Zoomcamp — Module 3: Orchestration with Mage

## Project Overview
We are working through the MLOps Zoomcamp course, Module 3. The goal is to wrap
`duration-prediction.py` into a production-style ML pipeline using Mage as the
orchestrator, running on AWS EC2.

## AWS Infrastructure

### EC2 Instance
- **Instance ID:** i-048cc37228103a941
- **Type:** t3.small (2 vCPU, 2GB RAM)
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
