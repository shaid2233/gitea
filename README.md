# Gitea & MySQL Health Check Service

A complete solution for deploying a self-hosted Gitea instance with MySQL database on Kubernetes, along with a database health check service and automated CI/CD workflows.

## Project Overview

This project consists of two main components:

### Part I – Gitea Deployment & Runner
- Self-hosted Gitea service with MySQL database on Kubernetes
- Persistent storage configuration
- Secrets management
- Ingress and DNS setup
- Resource monitoring
- Gitea Runner for CI/CD pipelines

### Part II – Database Health Check Service & CI/CD
- Flask-based microservice for MySQL connectivity checks
- Automated GitHub Actions workflows
- Docker image building and deployment
- Kubernetes manifest updates

## Prerequisites

- Kubernetes cluster
- Docker
- kubectl CLI tool
- Python 3.x
- pip (Python package manager)
- MySQL Server

## Installation & Setup

### 1. Gitea & MySQL Deployment

#### Create Required Namespaces
```bash
kubectl create namespace gitea
kubectl create namespace db
kubectl create namespace gitea-runner
```

#### Deploy Storage
```bash
# Apply PV and PVC for Gitea
kubectl apply -f gitea-pv.yaml
kubectl apply -f gitea-pvc.yaml

# Apply PV and PVC for MySQL
kubectl apply -f mysql-pv.yaml
kubectl apply -f mysql-pvc.yaml
```

#### Deploy Secrets
```bash
kubectl apply -f mysql-secret.yaml
kubectl apply -f gitea-secret.yaml
```

#### Deploy Applications
```bash
# Deploy MySQL
kubectl apply -f mysql-statefulset.yaml
kubectl apply -f mysql-service.yaml

# Deploy Gitea
kubectl apply -f gitea-deployment.yaml
kubectl apply -f gitea-service.yaml
```

### 2. Install Ingress Controller
```bash
curl -o nginx-ingress.yaml https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
kubectl apply -f nginx-ingress.yaml
```

### 3. Configure Local DNS
Add to your hosts file (`C:\Windows\System32\drivers\etc\hosts` on Windows):
```
127.0.0.1 gitea.local
```

### 4. Install Metrics Server
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### 5. Database Health Check Service

#### Environment Variables
Create a `.env` file:
```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=123456
DB_NAME=testdb
SERVER_HOST=localhost
SERVER_PORT=5000
```

#### Run the Service
```bash
# Install dependencies
pip install -r requirements.txt

# Start the service
python app.py
```

## CI/CD Workflows

The project includes three GitHub Actions workflows:

1. **Docker Build and Push**: Builds and pushes Docker images on main/master branch pushes
2. **MySQL and Pytest**: Runs tests on pull requests
3. **Deployment Manifest Update**: Updates Kubernetes manifests with new image tags

### Required Secrets

Set up the following GitHub secrets:
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `OTHER_REPO_PAT`
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- `MYSQL_DATABASE`

## API Endpoints

### Health Check Endpoint
- **URL**: `/is-db-alive`
- **Method**: GET
- **Success Response**: 
  - Code: 200
  - Content: Database connection successful
- **Error Response**: 
  - Code: 500
  - Content: Database connection failed

## Monitoring

Check the health of your deployments:
```bash
kubectl get pods -n gitea
kubectl get pods -n db
kubectl top pod -n gitea
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

1. If Gitea pods aren't starting, check the logs:
   ```bash
   kubectl logs -n gitea <pod-name>
   ```

2. For database connectivity issues:
   ```bash
   kubectl logs -n db <mysql-pod-name>
   ```

3. To verify ingress setup:
   ```bash
   kubectl get ingress -n gitea
   ```

## Security Notes

- Change default passwords in production
- Use proper SSL/TLS certificates
- Review and adjust RBAC permissions as needed
- Keep all components updated to their latest stable versions

## License

[Add your license details here]

## Support

For support, please open an issue in the GitHub repository.
