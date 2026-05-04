# AWS ECS Deployment Notes

This folder contains production deployment scaffolding for ECS Fargate.

## Target Architecture

- API Gateway or Application Load Balancer as public entry point.
- ECS Fargate service for the FastAPI backend.
- ECR repositories for backend and frontend images.
- RDS PostgreSQL with pgvector enabled.
- AWS Secrets Manager for `OPENAI_API_KEY` and `DATABASE_URL`.
- CloudWatch Logs for container logs.
- Private subnets for ECS tasks and RDS.

## Required Secrets

Create these Secrets Manager entries:

```text
judiciary-ai/openai-api-key
judiciary-ai/database-url
```

`DATABASE_URL` should point to the RDS PostgreSQL database, for example:

```text
postgresql://<user>:<password>@<rds-endpoint>:5432/judiciary_ai
```

## RDS pgvector

Run the SQL in `infra/postgres/init.sql` against the RDS database before
ingestion:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

The same script creates the `rag_chunks` table and HNSW vector index.

## Deployment Flow

1. Build and push backend image to ECR.
2. Build and push frontend image to ECR or deploy static assets to S3/CloudFront.
3. Register the ECS task definition from `ecs-task-definition.json`.
4. Create or update the ECS service.
5. Run `scripts/ingest_policies_pgvector.py` as a one-off task or controlled batch job.
6. Verify `/health`.
7. Run a smoke request through the load balancer/API Gateway.

## Production Controls

- Use task roles instead of static AWS credentials.
- Store all secrets in Secrets Manager.
- Keep ECS tasks in private subnets.
- Restrict RDS security group ingress to ECS task security groups.
- Enable CloudWatch log retention.
- Add alarms on 5xx rate, task restarts, high latency, and failed ingestion jobs.

