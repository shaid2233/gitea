
---

## Project Overview

This project covers multiple integration points and workflows:

1. **Gitea & MySQL on Kubernetes**  
   - Deploy Gitea with a NodePort service and an Nginx Ingress.
   - Deploy MySQL with a PersistentVolumeClaim (PVC) and secure credentials (stored in Kubernetes Secrets).
   - Enhance deployments with liveness/readiness probes and resource limits.

2. **Docker Hub Integration in CI/CD**  
   - Authenticate to Docker Hub using stored secrets.
   - Build, tag (using unique Git commit hashes), and push Docker images automatically.

3. **Flask Database Health Check Service**  
   - A Python Flask app that verifies MySQL connectivity by checking database accessibility, authentication, and service status.
   - Containerize the application using a Dockerfile and run it on port 5000.

4. **Gitea Runner in Kubernetes**  
   - Deploy a specialized runner (with Docker-in-Docker support) in its own namespace to execute CI/CD jobs.

5. **CI/CD Pipeline for MySQL Alive Container Deployment**  
   - Automate the process of generating a unique Docker tag, building and pushing a `mysql-alive` image to Docker Hub, and updating the Kubernetes deployment manifest.

6. **Enhancing Gitea Deployment on Kubernetes**  
   - Implement liveness and readiness probes to ensure pod health.
   - Set resource requests/limits to prevent overconsumption.
   - Install and patch the metrics-server for accurate resource monitoring.

7. **Running the CI/CD Pipeline on feat-branch in Gitea**  
   - Configure the CI/CD workflow to trigger on the feature branch.
   - Address connectivity issues by using the Node IP instead of the service FQDN.

---

## Architecture & Components

- **Gitea Deployment**:  
  Runs in a dedicated namespace (e.g., `gitea`), with external access via NodePort and Ingress.

- **MySQL Deployment**:  
  Uses persistent storage (PVC) and secure credentials stored as Kubernetes Secrets.

- **Flask Health Check Service**:  
  Checks if MySQL is accessible on port 3306. Returns HTTP 200 if successful, otherwise HTTP 500.

- **Gitea Runner**:  
  A Kubernetes-based runner in the `gitea-runner` namespace that handles CI/CD jobs with Docker socket access.

- **CI/CD Pipelines**:  
  Automated workflows for:
  - Docker Hub authentication, image building, and pushing.
  - Kubernetes deployment updates.
  - Running unit/integration tests for the Flask service.
  - Deploying a MySQL Alive container.

- **Metrics Server & Resource Management**:  
  Configured to monitor resource usage and ensure stable deployments.

---

## Prerequisites

- A running Kubernetes cluster.
- [kubectl](https://kubernetes.io/docs/tasks/tools/) configured for your cluster.
- (Optional) [K9s](https://k9scli.io/) for enhanced cluster management:
  ```bash
  choco install k9s -y
  k9s version
  ```
- Docker installed locally (for container builds and testing).
- Python 3.7+ for running the Flask app and tests.
- A Docker Hub account with an access token.
- A GitHub Personal Access Token (PAT) for repository operations.

---

## Deployment and Configuration Steps

### 1. Deploying Gitea & MySQL on Kubernetes

#### Gitea Deployment

- **Gitea Deployment YAML**:  
  Create and apply a deployment file for Gitea that includes your container image and service definitions (e.g., NodePort).  
  *Example Ingress Configuration (`gitea-ingress.yaml`):*
  ```yaml
  apiVersion: networking.k8s.io/v1
  kind: Ingress
  metadata:
    name: gitea-ingress
    namespace: gitea
    annotations:
      nginx.ingress.kubernetes.io/rewrite-target: /
  spec:
    rules:
      - host: gitea.local
        http:
          paths:
            - path: /
              pathType: Prefix
              backend:
                service:
                  name: gitea-nodeport-service
                  port:
                    number: 3000
  ```
  Apply the Ingress:
  ```bash
  kubectl apply -f gitea-ingress.yaml
  ```

#### MySQL Setup

- **PersistentVolumeClaim (`pvc-mysql.yaml`):**
  ```yaml
  apiVersion: v1
  kind: PersistentVolumeClaim
  metadata:
    name: mysql-pvc
    namespace: gitea
  spec:
    accessModes:
      - ReadWriteOnce
    resources:
      requests:
        storage: 10Gi
  ```
  Apply with:
  ```bash
  kubectl apply -f pvc-mysql.yaml
  ```

- **MySQL Credentials Secret (`mysql-secret.yaml`):**
  ```yaml
  apiVersion: v1
  kind: Secret
  metadata:
    name: mysecret
  type: Opaque
  data:
    MYSQL_ROOT_PASSWORD: cm9vdHBhc3N3b3Jk   # "rootpassword" (Base64 encoded)
    MYSQL_DATABASE: Z2l0ZWE=                # "gitea" (Base64 encoded)
    MYSQL_USER: Z2l0ZWF1c2Vy                # "giteauser" (Base64 encoded)
    MYSQL_PASSWORD: Z2l0ZWFwYXNzd29yZA==    # "giteapassword" (Base64 encoded)
  ```
  Apply with:
  ```bash
  kubectl apply -f mysql-secret.yaml
  ```

---

### 2. Enhancing Gitea Deployment on Kubernetes

#### 2.1 Implementing Liveness and Readiness Probes

- **Liveness Probe:**  
  Verifies that the pod is still running. If it fails, Kubernetes restarts the pod.

- **Readiness Probe:**  
  Ensures that the pod is fully initialized and ready to accept traffic before routing requests.

These probes help improve stability and reliability.

#### 2.2 Resource Management for Gitea

- **Resource Limits:**  
  To prevent Gitea from consuming excessive resources, add explicit resource limits to the deployment:
  ```yaml
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi
  ```
  This configuration ensures that Gitea requests a minimum of 100m CPU and 256Mi memory while capping its maximum consumption at 500m CPU and 512Mi memory.

#### 2.3 Installing and Configuring Metrics Server

- **Install Metrics Server:**  
  Apply the manifest:
  ```bash
  kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
  ```
  
- **Patch the Metrics Server Deployment:**  
  Resolve issues by enabling insecure TLS and updating the probe ports:
  ```bash
  kubectl patch deployment metrics-server -n kube-system --type=json -p='[
    {
      "op": "add",
      "path": "/spec/template/spec/containers/0/args/-",
      "value": "--kubelet-insecure-tls"
    },
    {
      "op": "replace",
      "path": "/spec/template/spec/containers/0/livenessProbe/httpGet/port",
      "value": 10250
    },
    {
      "op": "replace",
      "path": "/spec/template/spec/containers/0/readinessProbe/httpGet/port",
      "value": 10250
    }
  ]'
  ```

#### 2.4 Evaluating Load and Scaling

- **Monitoring:**  
  Use the metrics-server (or deploy Prometheus/Grafana for advanced monitoring) to view resource usage.
  
- **Scaling Strategies:**  
  Options include configuring a Horizontal Pod Autoscaler (HPA) to dynamically scale based on CPU/memory usage.
  
- **Verification:**  
  Use a command such as:
  ```bash
  watch kubectl top pod gitea-deployment-<pod-id> -n gitea
  ```
  to track resource usage in real time.

- **Access Check:**  
  Verify that the deployment is stable by accessing [http://gitea.local](http://gitea.local).

---

### 3. Configuring Docker Hub Authentication in Gitea CI/CD

#### Generate a Docker Hub Access Token

- Log in to Docker Hub → Account Settings → Access Tokens.
- Create a token (e.g., `ci/cd gitea`) and record the credentials.

#### Store Credentials as Repository Secrets

- In your Gitea repository, navigate to **Settings → Actions → Secrets**.
- Add:
  - `DOCKERHUB_USERNAME`
  - `DOCKERHUB_TOKEN`

#### Sample Workflow for Docker Hub Authentication

Create `.gitea/workflows/docker-build-push.yaml`:

```yaml
name: Docker Build and Push

on:
  push:
    branches:
      - main
      - master

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Authenticate with Docker Hub
        run: |
          echo ${{ secrets.DOCKERHUB_TOKEN }} | docker login --username ${{ secrets.DOCKERHUB_USERNAME }} --password-stdin
          if [ $? -eq 0 ]; then
            echo "Successfully authenticated with Docker Hub"
          else
            echo "Authentication failed"
            exit 1
          fi

      - name: Get unique image tag
        id: vars
        run: |
          UNIQUE_TAG=$(git rev-parse --short HEAD)
          echo "UNIQUE_TAG=${UNIQUE_TAG}" >> $GITHUB_ENV

      - name: Build Docker image
        run: |
          docker build -t ${{ secrets.DOCKERHUB_USERNAME }}/python-app:${{ env.UNIQUE_TAG }} .

      - name: Push Docker image to Docker Hub
        run: |
          docker push ${{ secrets.DOCKERHUB_USERNAME }}/python-app:${{ env.UNIQUE_TAG }}

      - name: Logout from Docker Hub
        run: |
          docker logout
```

---

### 4. Flask Database Health Check Service

#### Overview

This Flask application checks if a MySQL database is accessible on port 3306 by verifying:

- Database connectivity.
- Correct authentication credentials.
- That the database service is running.

It returns HTTP 200 if all checks pass; otherwise, it returns HTTP 500.

#### Running MySQL in a Docker Container

```bash
docker run -d \
  --name mysql-test \
  -e MYSQL_ROOT_PASSWORD=123456 \
  -e MYSQL_DATABASE=testdb \
  -p 3306:3306 \
  mysql:8.0
```

#### Dockerfile for the Flask App

```dockerfile
# Use an official Python base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /usr/src/app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set environment variables (override at runtime for sensitive data)
ENV DB_HOST=localhost
ENV DB_PORT=3306
ENV DB_USER=root
ENV DB_PASSWORD=123456

# Expose port 5000 for the Flask app
EXPOSE 5000

# Run the application
CMD ["python", "main.py"]
```

#### Build and Run the Flask Container

```bash
docker build -t my-app .
docker run -d -p 5000:5000 my-app
```

> **Note:**  
> If the Flask app cannot connect to MySQL, consider running both containers on the same Docker network (or using host networking).

---

### 5. Setting Up a Gitea Runner in Kubernetes

#### Create the Gitea Runner Namespace

```bash
kubectl create namespace gitea-runner
```

#### Generate the Gitea Runner Token

- Log in as an admin in Gitea.
- Navigate to **Site Admin → Actions → Runner → Create New Runner**.
- Generate a runner registration token and record it.

#### Deploy the Gitea Runner

Create `gitea-runner.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gitea-runner
  namespace: gitea-runner
  labels:
    app: gitea-runner
spec:
  replicas: 1
  selector:
    matchLabels:
      app: gitea-runner
  template:
    metadata:
      labels:
        app: gitea-runner
    spec:
      containers:
      - name: gitea-runner
        image: gitea/act_runner:latest
        securityContext:
          privileged: true
        env:
        - name: GITEA_INSTANCE_URL
          value: "http://<your-gitea-server-url>"  # Replace with your actual Gitea URL
        - name: GITEA_RUNNER_REGISTRATION_TOKEN
          value: "os30pW4A2b4nwwAynRFrnjP9J7Q8CS0wqoKw6jIZ"  # Replace with your runner token
        - name: GITEA_RUNNER_NAME
          value: "gitea-runner-1"
        volumeMounts:
        - name: docker-socket
          mountPath: /var/run/docker.sock
        - name: runner-home
          mountPath: /data
      volumes:
      - name: docker-socket
        hostPath:
          path: /var/run/docker.sock
      - name: runner-home
        emptyDir: {}
```

Deploy the runner:

```bash
kubectl apply -f gitea-runner.yaml
kubectl get pods -n gitea-runner
```

---

### 6. CI/CD Pipeline for Database Health Check Service

This GitHub Actions workflow automates the following steps:

- Starts a MySQL test container.
- Builds the Flask app Docker image.
- Runs integration tests using `pytest`.

Create `.github/workflows/ci.yaml`:

```yaml
name: Database Health Check CI

on: 
  pull_request:
    types: [opened, reopened, synchronize]
    branches:
      - main
      - dev

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Start MySQL
        run: |
          docker run -d \
            --name mysql-test \
            --network host \
            -e MYSQL_ROOT_PASSWORD=$DB_PASSWORD \
            -e MYSQL_DATABASE=$MYSQL_DATABASE \
            -p 3306:3306 \
            mysql:8.0

      - name: Wait for MySQL to be ready
        run: |
          for i in {1..30}; do
            if docker exec mysql-test mysqladmin ping -h $DB_HOST -u $DB_USER -p$DB_PASSWORD --silent; then
              echo "MySQL is ready"
              break
            fi
            echo "Waiting for MySQL to be ready..."
            sleep 1
          done

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.9

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Build Docker image
        run: |
          docker builder prune -f
          docker build --no-cache -t flask-app .

      - name: Start Flask app in the background
        run: |
          docker run -d --network host -p 5000:5000 --name flask-container flask-app

      - name: Run tests
        run: |
          pytest tests/test_app.py
```

---

### 7. CI/CD Pipeline for MySQL Alive Container Deployment

This pipeline automates building, tagging, pushing, and deploying a **MySQL Alive** container. It is triggered on every push to the `dev` or `main` branches and consists of three jobs.

#### Trigger Conditions

```yaml
on:
  push:
    branches:
      - dev
      - main
```

#### Job 1: Generate a Unique Tag

Extract a shortened Git commit hash and save it as an output.

```yaml
jobs:
  job1:
    runs-on: ubuntu-latest
    outputs:
      UNIQUE_TAG: ${{ steps.generate_tag.outputs.UNIQUE_TAG }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Generate unique tag
        id: generate_tag
        run: |
          UNIQUE_TAG=$(git rev-parse --short HEAD)
          echo "UNIQUE_TAG=${UNIQUE_TAG}" >> $GITHUB_OUTPUT
```

#### Job 2: Build & Push Docker Image

Build the Docker image using the tag from Job 1 and push it to Docker Hub.

```yaml
  job2:
    runs-on: ubuntu-latest
    needs: job1
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        
      - name: Use tag from job1
        run: |
          echo "Using tag: ${{ needs.job1.outputs.UNIQUE_TAG }}"

      - name: Authenticate with Docker Hub
        env:
          DOCKERHUB_TOKEN: ${{ secrets.DOCKERHUB_TOKEN }}
          DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
        run: |
          echo "${DOCKERHUB_TOKEN}" | docker login --username "${DOCKERHUB_USERNAME}" --password-stdin
          if [ $? -eq 0 ]; then
            echo "Successfully authenticated with Docker Hub"
          else
            echo "Authentication failed"
            exit 1
          fi

      - name: Build Docker image
        run: |
          docker build -t ${{ secrets.DOCKERHUB_USERNAME }}/mysql-alive:${{ needs.job1.outputs.UNIQUE_TAG }} .

      - name: Push Docker image to Docker Hub
        run: |
          docker push ${{ secrets.DOCKERHUB_USERNAME }}/mysql-alive:${{ needs.job1.outputs.UNIQUE_TAG }}

      - name: Logout from Docker Hub
        run: |
          docker logout
```

#### Job 3: Update Kubernetes Deployment

Update the Kubernetes deployment manifest with the new image tag and commit the changes.

```yaml
  job3:
    needs: job2 
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Kubernetes manifest repo
        uses: actions/checkout@v4
        with:
          repository: shaid2233/k8s-mysql-alive
          token: ${{ secrets.OTHER_REPO_PAT }}
          ref: ${{ github.ref_name }}

      - name: Setup yq
        uses: dcarbone/install-yq-action@v1.3.0

      - name: Modify deployment tag
        env:
          UNIQUE_TAG: ${{ needs.job1.outputs.UNIQUE_TAG }}
          DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
        run: |
          echo "Updating deployment.yaml with tag: $UNIQUE_TAG"
          yq e ".spec.template.spec.containers[0].image = \"$DOCKERHUB_USERNAME/mysql-alive:$UNIQUE_TAG\"" -i deployment.yaml

      - name: Set up Git configuration
        run: |
          git config --global user.name "shaid2233"  
          git config --global user.email "shaidaniel27@gmail.com"

      - name: Commit and push changes
        run: |
          git status
          git add .
          git commit -m "Update MySQL image tag to mysql-alive:$UNIQUE_TAG"
          git push
        env:
          GITHUB_TOKEN: ${{ secrets.OTHER_REPO_PAT }}
```

---

### 8. Running the CI/CD Pipeline on feat-branch in Gitea

#### Branch Setup

- **Branches:**  
  - `main` – Production-ready branch  
  - `dev` – Development branch  
  - `feat-branch` – Feature branch for new changes

All branches initially contain the same codebase.

#### CI/CD Pipeline Configuration

Create a workflow file under `.gitea/workflows/` (for example, `.gitea/workflows/ci.yaml`):

```yaml
on:
  push:
    branches:
      - main
      - feat-branch

jobs:
  build:
    runs-on: ubuntu-20.04
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Quick Verification
        run: echo "Pipeline is optimized and running!"
```

#### Resolving Connectivity Issues: Node IP vs. Service FQDN

- **Initial Approach (Service FQDN):**  
  Attempted to use:
  ```
  http://gitea-nodeport-service.gitea.svc.cluster.local:3000
  ```
  but encountered DNS resolution issues.

- **Solution: Using the Node IP:**  
  Switched to:
  ```
  http://192.168.65.3:30003
  ```
  which bypassed DNS resolution and provided direct access to the service.

**Why the Node IP Works Better:**

- **Direct Access:**  
  It provides a direct route to the service, eliminating the dependency on Kubernetes DNS resolution.
- **Bypassing DNS Issues:**  
  Avoids potential misconfigurations or network policies blocking DNS traffic.
- **Reliability:**  
  Offers a simpler and more reliable method for testing and debugging.

---

## Environment Variables and Secrets

| Variable             | Description                                          |
|----------------------|------------------------------------------------------|
| `DOCKERHUB_USERNAME` | Docker Hub username                                  |
| `DOCKERHUB_TOKEN`    | Docker Hub access token                              |
| `OTHER_REPO_PAT`     | GitHub Personal Access Token for the Kubernetes repo |
| `UNIQUE_TAG`         | Git commit hash used as a version tag                |

---

## Troubleshooting & Tips

- **Networking Issues:**  
  If containers cannot communicate, verify they are on the same Docker network or use host networking for local testing.

- **Persistent Data:**  
  Ensure your PersistentVolumeClaims are correctly bound and that storage is available for MySQL.

- **Docker Build Errors:**  
  Confirm that the `Dockerfile` is in the repository root and that all necessary files are present.

- **CI/CD Connectivity:**  
  Ensure repository checkouts (using `actions/checkout@v3` or `v4`) and environment variables are correctly configured.

- **Secret Management:**  
  Always use environment variables and repository secrets for sensitive credentials rather than hardcoding them.

---

## License

This project is provided for educational purposes. You are free to modify and use it as needed.

---

Happy coding and deploying! 🚀
```

---
