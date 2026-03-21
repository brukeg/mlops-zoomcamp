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
- **Project name:** mlops-pipeline
- **Default credentials:** admin@admin.com / (change this!)
- **Commands:**
```bash
  docker ps                    # check if running
  docker logs mage             # view logs
  docker stop mage             # stop
  docker start mage            # start
  docker restart mage          # restart
```

## Key Files
- **Pipeline script:** `mlops-zoomcamp/03-orchestration/duration-prediction.py`
- **MLflow start script:** `/usr/local/bin/start-mlflow.sh` (on EC2)
- **MLflow systemd unit:** `/etc/systemd/system/mlflow.service` (on EC2)

## Known Issues / Deferred Work
1. **RDS password visible in ps aux** — pass via environment variable or .pgpass
   instead of CLI argument in start-mlflow.sh
2. **train/val date window bug** — current script uses month+1 for validation,
   but course spec says train=2 months ago, val=1 month ago. Fix before
   wiring into Mage scheduler.
3. **Mage default password** — change from default admin credentials

## Startup Checklist (Each Session)
1. Start RDS in AWS console, wait for "Available"
2. Start EC2 in AWS console, grab new Public DNS
3. SSH in and verify services:
```bash
   sudo systemctl status mlflow
   docker ps
```
4. If first session after password rotation, update Secrets Manager

## Shutdown Checklist (Each Session)
1. `exit` SSH session
2. Stop EC2 instance in AWS console
3. Stop RDS instance in AWS console
