# MLFlow on Remote Server

## Connect to EC2 with SSH
- from the `~/.ssh` directory

```bash
ssh -i "mlflow-key-pair-oregon.pem" ec2-user@<PUBLIC-IPv4-DNS>
```

## Spin up the MLFlow server
```bash
mlflow server -h 0.0.0.0 -p 5000 \
  --backend-store-uri postgresql://mlflow:G3lZvLp3ZXqLzHzCc0mT@mlflow-backend-db.c1aw8egmm7x1.us-west-2.rds.amazonaws.com:5432/mlflow_db \
  --default-artifact-root s3://mlflow-artifacts-remote-bruke-720881264075-us-west-2-an
```

## Stop Infrastructure
- AWS charges for up time on both RDS and EC2, so stop them when you're not actively using them

#### EC2
- From the EC2 console: Instances > select the instance check box (`i-048cc37228103a941`) > click Instance State > Stop instance.
- Wait for it to confirm 
#### RDS
- From the RDS console: Database > select the database check box (mlflow-backend-db) > click Actions > Stop Temporarily
- Wait for it to confirm (usually takes several minutes)
- For some ungodly reason Jeff decided that RDS can't be deactivate indefinitely, so it will come back on line 7 days from when it was stopped.
- It is possible to create a snapshot of database and restore from that snapshot. 
  - Instead of temporarily deactivating you would take a snapshot, destroy the current db instance, later restore from the snapshot, rinse & repeat. 

### My EC2 public DNS
- Looks something like this: ec2-user@ec2-35-85-32-230.us-west-2.compute.amazonaws.com
- This part: `ec2-35-85-32-230.us-west-2.compute.amazonaws.com` will change every time you stop and restart your instance
- Grab the public IPv4 DNS from the EC2 console under Instances


### Access the mlflow tracking server at this address:
- http://ec2-user@<PUBLIC-IPv4-DNS>:5000


# Considerations

## Security
- Restrict access to the server through a VPN/C
- Use Https://

## Scalability
- How many people or teams will use the server?

## Isolation
- Define standards for naming experiments, models, and a set of default tags (team-name-model-name-version, etc.)
- Restrict access to artifacts (eg. use S3buckets living in different AWS accounts)


## Limitations
- Authenticatin, Users, Teams: the open source self hosted version of MLFlow doesn't support these concepts.
- Data Versioning: to ensure full reproducibility you need to versin your data
- Data/Model Monitoring & Alerting: out of scope for MLFlow
