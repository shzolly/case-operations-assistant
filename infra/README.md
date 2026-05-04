# Infrastructure Plan

## Local

- Backend service on port 8000.
- Frontend service on port 5173.
- Future Docker Compose stack with backend, frontend, mock legacy API, and database.

## AWS Target

- API Gateway as public entry point.
- ECS Fargate for backend and mock/adapter services.
- Secrets Manager for model and database credentials.
- Private subnets for service tasks.
- CloudWatch logs and metrics.
- OpenTelemetry traces exported to the chosen backend.

See `infra/aws` for ECS task definition scaffolding, Secrets Manager notes, and
deployment workflow guidance.
