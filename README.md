```markdown
# Complete Project Documentation

This repository contains two primary components:

1. **Part I – Gitea Deployment & Runner**  
   Deploys a self-hosted Git service (Gitea) along with its supporting MySQL database on Kubernetes. It includes persistent storage, namespace isolation, secrets management, ingress and DNS configuration, resource monitoring, and a Gitea Runner for executing CI/CD pipelines.

2. **Part II – Database Health Check Service & CI/CD Workflows**  
   A Flask-based microservice to check MySQL connectivity and a set of GitHub Actions workflows that automatically build Docker images, run tests, and update Kubernetes manifests with unique image tags.

---

## Table of Contents

- [Part I – Gitea Deployment & Runner](#part-i--gitea-deployment--runner)
  - [1. Persistent Storage Setup](#1-persistent-storage-setup)
    - [A. Gitea Storage](#a-gitea-storage)
    - [B. MySQL Storage](#b-mysql-storage)
  - [2. Deploying Gitea & MySQL](#2-deploying-gitea--mysql)
    - [A. Gitea Namespace & Deployment](#a-gitea-namespace--deployment)
    - [B. Gitea Service](#b-gitea-service)
    - [C. MySQL StatefulSet & Service](#c-mysql-statefulset--service)
  - [3. Secrets Management](#3-secrets-management)
    - [A. MySQL Secret](#a-mysql-secret)
    - [B. Gitea Database Secret](#b-gitea-database-secret)
  - [4. Ingress Installation & Local DNS Configuration](#4-ingress-installation--local-dns-configuration)
    - [A. Installing the NGINX Ingress Controller](#a-installing-the-nginx-ingress-controller)
    - [B. Gitea Ingress Configuration](#b-gitea-ingress-configuration)
    - [C. Local DNS Configuration](#c-local-dns-configuration)
  - [5. Monitoring & Resource Management](#5-monitoring--resource-management)
    - [A. Health Probes](#a-health-probes)
    - [B. Resource Requests and Limits](#b-resource-requests-and-limits)
    - [C. Metrics Server Installation](#c-metrics-server-installation)
  - [6. Setting Up a Gitea Runner](#6-setting-up-a-gitea-runner)
- [Part II – Database Health Check Service & CI/CD Workflows](#part-ii--database-health-check-service--ci-cd-workflows)
  - [1. Database Health Check Service](#1-database-health-check-service)
    - [Features](#features)
    - [Prerequisites](#prerequisites)
    - [Environment Variables](#environment-variables)
    - [Installation & Running](#installation--running)
    - [API Endpoint](#api-endpoint)
    - [Running Tests](#running-tests)
  - [2. GitHub Actions Workflows](#2-github-actions-workflows)
    - [Docker Build and Push Workflow](#docker-build-and-push-workflow)
    - [MySQL and Pytest Workflow](#mysql-and-pytest-workflow)
    - [Deployment Manifest Update Workflow](#deployment-manifest-update-workflow)

---

## Part I – Gitea Deployment & Runner

This section covers the deployment of a Gitea instance with its supporting MySQL database on Kubernetes, including persistent storage, secrets, ingress, monitoring, and the setup of a Gitea Runner.

### 1. Persistent Storage Setup

#### A. Gitea Storage

**What We Did:**  
A PersistentVolume (PV) reserves 5Gi from a local directory, and a PersistentVolumeClaim (PVC) in the `gitea` namespace ensures that Gitea’s data persists across pod restarts.

**Gitea PersistentVolume (PV):**

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: gitea-pv
  labels:
    name: gitea-pv
spec:
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: hostpath
  local:
    path: "/c/yourDir/gitea"  # Update this path to a directory on your computer
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
          - key: kubernetes.io/hostname
            operator: In
            values:
              - docker-desktop
```

**Gitea PersistentVolumeClaim (PVC):**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: gitea-data-pvc
  namespace: gitea
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: hostpath
```

**Deployment Steps:**

1. Create the `gitea` namespace:
   ```bash
   kubectl create namespace gitea
   ```
2. Apply the PV and PVC files:
   ```bash
   kubectl apply -f <path-to-gitea-pv.yaml>
   kubectl apply -f <path-to-gitea-pvc.yaml>
   ```

#### B. MySQL Storage

**What We Did:**  
A PersistentVolume (PV) for MySQL reserves 10Gi from a local directory, and a PersistentVolumeClaim (PVC) in the `db` namespace ensures data persistence.

**MySQL PersistentVolume (PV):**

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mysql-pv
  namespace: db
  labels:
    name: mysql-pv
spec:
  storageClassName: hostpath
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  local:
    path: "/c/yourDir/mysql"  # Update this path to a directory on your computer
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
          - key: kubernetes.io/hostname
            operator: In
            values:
              - docker-desktop
```

**MySQL PersistentVolumeClaim (PVC):**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
  namespace: db
spec:
  storageClassName: hostpath
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

**Deployment Steps:**

1. Create the `db` namespace:
   ```bash
   kubectl create namespace db
   ```
2. Apply the PV and PVC files:
   ```bash
   kubectl apply -f <path-to-mysql-pv.yaml>
   kubectl apply -f <path-to-mysql-pvc.yaml>
   ```

---

### 2. Deploying Gitea & MySQL

#### A. Gitea Namespace & Deployment

**Create the Gitea Namespace:**

```bash
kubectl create namespace gitea
```

**Gitea Deployment YAML:**

This deployment mounts the PVC, sources environment variables from a secret for the database connection, and configures health probes and resource limits.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gitea-deployment
  namespace: gitea
  labels:
    app: gitea
spec:
  replicas: 1
  selector:
    matchLabels:
      app: gitea
  template:
    metadata:
      labels:
        app: gitea
    spec:
      volumes:
      - name: gitea-data
        persistentVolumeClaim:
          claimName: gitea-data-pvc
      containers:
      - name: gitea
        image: gitea/gitea:latest
        ports:
        - containerPort: 3000 
        volumeMounts:
        - name: gitea-data
          mountPath: /data
        env:
        - name: GITEA__database__DB_TYPE
          valueFrom:
            secretKeyRef:
              name: gitea-db-secret
              key: DB_TYPE
        - name: GITEA__database__HOST
          valueFrom:
            secretKeyRef:
              name: gitea-db-secret
              key: HOST
        - name: GITEA__database__NAME
          valueFrom:
            secretKeyRef:
              name: gitea-db-secret
              key: NAME
        - name: GITEA__database__USER
          valueFrom:
            secretKeyRef:
              name: gitea-db-secret
              key: USER
        - name: GITEA__database__PASSWD
          valueFrom:
            secretKeyRef:
              name: gitea-db-secret
              key: PASSWD
        livenessProbe:
          httpGet:
            path: /api/healthz
            port: 3000
          initialDelaySeconds: 120
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /api/healthz
            port: 3000
          initialDelaySeconds: 60
          periodSeconds: 10
          timeoutSeconds: 5
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
```

#### B. Gitea Service

Expose Gitea externally using a NodePort service:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: gitea-nodeport-service
  namespace: gitea
spec:
  selector:
    app: gitea
  ports:
  - protocol: TCP
    port: 3000
    targetPort: 3000
    nodePort: 30003
  type: NodePort
```

**Deploy Gitea:**

```bash
kubectl apply -f <path-to-gitea-deployment.yaml>
kubectl apply -f <path-to-gitea-service.yaml>
```

#### C. MySQL StatefulSet & Service

**Create the db Namespace:**

```bash
kubectl create namespace db
```

**MySQL StatefulSet YAML:**

Deploys a MySQL instance with credentials from a secret and uses a volume claim template for persistent storage.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
  namespace: db
spec:
  serviceName: "mysql"
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:5.7
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysecret
              key: MYSQL_ROOT_PASSWORD
        - name: MYSQL_DATABASE
          valueFrom:
            secretKeyRef:
              name: mysecret
              key: MYSQL_DATABASE
        - name: MYSQL_USER
          valueFrom:
            secretKeyRef:
              name: mysecret
              key: MYSQL_USER
        - name: MYSQL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysecret
              key: MYSQL_PASSWORD
        ports:
        - containerPort: 3306
        volumeMounts:
        - name: mysql-data
          mountPath: /var/lib/mysql
  volumeClaimTemplates:
  - metadata:
      name: mysql-data
    spec:
      storageClassName: hostpath
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 5Gi
```

**MySQL Service YAML:**

Expose MySQL using a NodePort service:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql
  namespace: db
spec:
  type: NodePort
  selector:
    app: mysql
  ports:
  - protocol: TCP
    port: 3306
    targetPort: 3306
    nodePort: 30037
```

**Deploy MySQL:**

```bash
kubectl apply -f <path-to-mysql-statefulset.yaml>
kubectl apply -f <path-to-mysql-service.yaml>
```

---

### 3. Secrets Management

Secrets securely store the sensitive information for MySQL and Gitea.

#### A. MySQL Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mysecret
  namespace: db  # Ensure this is the correct namespace for MySQL
type: Opaque
data:
  MYSQL_ROOT_PASSWORD: ############   # "rootpassword" (Base64 encoded)
  MYSQL_DATABASE: ############                 # "gitea" (Base64 encoded)
  MYSQL_USER: ############               # "giteauser" (Base64 encoded)
  MYSQL_PASSWORD: ############     # "giteapassword" (Base64 encoded)
```

#### B. Gitea Database Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: gitea-db-secret
  namespace: gitea  # Ensure this matches your Gitea deployment namespace
type: Opaque
stringData:
  DB_TYPE:############ 
  HOST: ############ 
  NAME: ############ 
  USER: ############ 
  PASSWD: ############ 
```

**Apply the Secrets:**

```bash
kubectl apply -f mysql-secret.yaml
kubectl apply -f gitea-secret.yaml
```

Verify creation:

```bash
kubectl get secrets -n db      # For MySQL secret
kubectl get secrets -n gitea   # For Gitea secret
```

---

### 4. Ingress Installation & Local DNS Configuration

#### A. Installing the NGINX Ingress Controller

Install the Ingress Controller with:

```bash
curl -o nginx-ingress.yaml https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
kubectl apply -f nginx-ingress.yaml
```

Verify the Ingress Controller pods:

```bash
kubectl get pods --namespace ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

#### B. Gitea Ingress Configuration

Create an Ingress resource to route external traffic from `gitea.local` to the Gitea NodePort service:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: gitea-ingress
  namespace: gitea
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

Deploy the Ingress:

```bash
kubectl apply -f gitea-ingress.yaml
```

#### C. Local DNS Configuration

For Windows 10, update the hosts file (`C:\Windows\System32\drivers\etc\hosts`) with:

```
127.0.0.1 gitea.local
```

Verify with:

```bash
ping gitea.local
```

Then access [http://gitea.local](http://gitea.local).

---

### 5. Monitoring & Resource Management

#### A. Health Probes

Gitea is configured with health probes:

```yaml
livenessProbe:
  httpGet:
    path: /api/healthz
    port: 3000
  initialDelaySeconds: 120
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /api/healthz
    port: 3000
  initialDelaySeconds: 60
  periodSeconds: 10
  timeoutSeconds: 5
```

#### B. Resource Requests and Limits

```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

#### C. Metrics Server Installation

Install the Metrics Server:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

For local development, patch for insecure kubelet TLS:

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

Verify:

```bash
kubectl get deployment metrics-server -n kube-system
kubectl top pod -n gitea
```

---

### 6. Setting Up a Gitea Runner

A Gitea Runner executes CI/CD actions from your Gitea instance.

#### A. Create the Gitea Runner Namespace

```bash
kubectl create namespace gitea-runner
```

#### B. Generate the Runner Token

- Log in as an admin in Gitea.
- Navigate to **Site Admin → Actions → Runner → Create New Runner**.
- Generate and record the registration token.

#### C. Gitea Runner Deployment

Create a file named `gitea-runner.yaml` with the following content:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gitea-runner
  namespace: gitea-runner
  labels:
    app: gitea-runner
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gitea-runner
  template:
    metadata:
      labels:
        app: gitea-runner
    spec:
      securityContext:
        fsGroup: 1000
      containers:
      - name: gitea-runner
        image: gitea/act_runner:latest
        securityContext:
          privileged: true
        env:
        - name: GITEA_INSTANCE_URL
          value: "http://<your-gitea-server-url>"  # Replace with your actual Gitea URL
        - name: GITEA_RUNNER_REGISTRATION_TOKEN
          value: "#################"  # Replace with your runner token
        - name: GITEA_RUNNER_NAME
          value: "gitea-runner"
        volumeMounts:
        - name: runner-home
          mountPath: /data
        - name: docker-sock
          mountPath: /var/run/docker.sock
      volumes:
      - name: runner-home
        emptyDir: {}
      - name: docker-sock
        hostPath:
          path: /var/run/docker.sock
          type: Socket
```

**Deploy the Runner:**

```bash
kubectl apply -f gitea-runner.yaml
```

Verify with:

```bash
kubectl get pods -n gitea-runner
```

---

## Part II – Database Health Check Service & CI/CD Workflows

This section documents a Flask microservice for checking MySQL connectivity and describes the GitHub Actions workflows used for building Docker images, running tests, and updating Kubernetes manifests.

### 1. Database Health Check Service

A Flask-based microservice exposes an endpoint to check MySQL database connectivity.

#### Features

- REST endpoint (`/is-db-alive`) to verify database connectivity.
- Configurable via environment variables.
- Automated tests with a retry mechanism.
- Docker-ready configuration.

#### Prerequisites

- Python 3.x
- MySQL Server
- pip (Python package manager)

#### Environment Variables

Set the following in your environment or a `.env` file:

```
DB_HOST=############      # MySQL host address
DB_PORT=############           # MySQL port
DB_USER=############           # MySQL user
DB_PASSWORD=############ ****     # MySQL password
DB_NAME=############         # Database name 
SERVER_PORT=5000       # Flask server port
```

#### Installation & Running

1. Clone the repository:

   ```bash
   git clone [repository-url]
   cd [repository-name]
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the Flask server:

   ```bash
   python app.py
   ```

The service will run at `http://localhost:5000`.

#### API Endpoint

**GET /is-db-alive**

- **200 OK:** Database connection successful.
- **500 Internal Server Error:** Database connection failed.

#### Running Tests

Tests are written using Pytest. Run them with:

```bash
pytest
```

---

### 2. GitHub Actions Workflows

This project includes several GitHub Actions workflows to automate Docker image builds, testing, and deployment manifest updates.

#### Docker Build and Push Workflow

This workflow triggers on pushes to the main or master branch and builds a Docker image for the Python application.

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
        run: docker logout
```

#### MySQL and Pytest Workflow

This workflow runs on pull requests to the `main` or `dev` branches. It starts a MySQL container, sets up Python, builds the Docker image, runs the Flask app, and executes tests.

```yaml
name: MySQL and pytest
on: 
  pull_request:
    types: [opened, reopened, synchronize]
    branches:
      - main
      - dev
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DB_HOST: ${{ secrets.DB_HOST }}
      DB_PORT: ${{ secrets.DB_PORT }}
      DB_USER: ${{ secrets.DB_USER }}
      DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
      MYSQL_ROOT_PASSWORD: ${{ secrets.MYSQL_ROOT_PASSWORD }}
      MYSQL_DATABASE: ${{ secrets.MYSQL_DATABASE }}
    steps:
      - uses: actions/checkout@v3
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
        run: pytest tests/test_app.py
```

#### Deployment Manifest Update Workflow

This workflow triggers on pushes to the `dev` or `main` branch. It generates a unique image tag, builds and pushes a Docker image for the health check service, and updates the Kubernetes deployment manifest in another repository.

```yaml
name: update deployment my-sql-alive
on:
  push:
    branches:
      - dev
      - main 
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
        run: docker logout
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
```

You can now copy the above content and paste it into your `README.md` file.
