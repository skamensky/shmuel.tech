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
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

helm install external-secrets \
   external-secrets/external-secrets \
    -n external-secrets \
    --create-namespace \


helm install external-dns bitnami/external-dns \
  --namespace kube-system \
  --set provider=google \
  --set google.project=kelev-dev \
  --set domainFilters[0]=shmuel.tech \
  --set policy=sync \
  --set txtOwnerId=shmuel-tech-cluster

helm repo update

kubectl -f  https://github.com/external-secrets/external-secrets/releases/latest/download/install.yaml

# Wait for the ArgoCD server deployment to become available
echo "Waiting for ArgoCD server to become available..."
kubectl wait --for=condition=available --timeout=600s deployment/argocd-server -n "$NAMESPACE"

echo "ArgoCD installation complete."
