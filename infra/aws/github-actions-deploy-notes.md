# GitHub Actions Deployment Plan

The current CI builds and scans images. A production deploy workflow should be
added once AWS account, ECR repositories, cluster names, and IAM roles are known.

Recommended workflow:

1. Configure GitHub OIDC to assume an AWS deploy role.
2. Build backend and frontend images.
3. Push images to ECR.
4. Render ECS task definition with image tags.
5. Deploy to ECS service.
6. Run post-deploy smoke tests.

Required GitHub variables:

```text
AWS_REGION
ECR_BACKEND_REPOSITORY
ECR_FRONTEND_REPOSITORY
ECS_CLUSTER
ECS_SERVICE
ECS_TASK_DEFINITION
```

Required GitHub environment protection:

- Manual approval for production deploys.
- Restricted reviewers.
- Separate staging and production environments.

