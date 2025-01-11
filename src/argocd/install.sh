#!/bin/bash
set -e
# Define namespace and ArgoCD manifest URL
NAMESPACE="argocd"
ARGOCD_MANIFEST_URL="https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
  echo "Creating namespace $NAMESPACE..."
  kubectl create namespace "$NAMESPACE"
else
  echo "Namespace $NAMESPACE already exists. Skipping creation."
fi

# Apply the ArgoCD manifest
echo "Applying ArgoCD manifest..."
kubectl apply -n "$NAMESPACE" -f "$ARGOCD_MANIFEST_URL"
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj-labs/applicationset/master/manifests/install.yaml

# Wait for the ArgoCD server deployment to become available
echo "Waiting for ArgoCD server to become available..."
kubectl wait --for=condition=available --timeout=600s deployment/argocd-server -n "$NAMESPACE"

echo "ArgoCD installation complete."
