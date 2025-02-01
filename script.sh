#!/bin/bash

# Define namespaces
GITEA_NAMESPACE="gitea"
DB_NAMESPACE="db"
RUNNER_NAMESPACE="gitea-runner"

# Create the namespaces
echo "Creating namespaces..."
kubectl create namespace $GITEA_NAMESPACE
kubectl create namespace $DB_NAMESPACE
kubectl create namespace $RUNNER_NAMESPACE

# Apply Persistent Volume (PV) and Persistent Volume Claim (PVC) for Gitea
echo "Applying gitea-pv.yaml and gitea-pvc.yaml..."
kubectl apply -f gitea-pv.yaml --namespace $GITEA_NAMESPACE
kubectl apply -f gitea-pvc.yaml --namespace $GITEA_NAMESPACE

# Apply Persistent Volume (PV) and Persistent Volume Claim (PVC) for MySQL
echo "Applying mysql-pv.yaml and mysql-pvc.yaml..."
kubectl apply -f mysql-pv.yaml --namespace $DB_NAMESPACE
kubectl apply -f mysql-pvc.yaml --namespace $DB_NAMESPACE

# Apply MySQL StatefulSet (in the db namespace)
echo "Applying mysql.yaml for database..."
kubectl apply -f mysql.yaml --namespace $DB_NAMESPACE

# Apply Gitea Deployment (in the gitea namespace)
echo "Applying gitea.yaml..."
kubectl apply -f gitea.yaml --namespace $GITEA_NAMESPACE

# Install the NGINX Ingress Controller in the Gitea namespace
echo "Installing NGINX Ingress Controller in the gitea namespace..."
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install nginx-ingress ingress-nginx/ingress-nginx --namespace $GITEA_NAMESPACE

# Apply Ingress resource
echo "Applying ingress.yaml..."
kubectl apply -f ingress.yaml --namespace $GITEA_NAMESPACE

# Apply Gitea Runner Deployment in the gitea-runner namespace
echo "Applying gitea-runner.yaml..."
kubectl apply -f gitea-runner.yaml --namespace $RUNNER_NAMESPACE

echo "All resources have been applied successfully!"

