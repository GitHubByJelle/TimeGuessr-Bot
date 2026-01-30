# Installation & Deployment Guide

This document explains how to deploy the infrastructure and container job for this project using Azure CLI, Bicep, and Azure Container Apps Jobs.

⚠️ **Security notice**
- Never commit secrets, `.env` files, webhook URLs, or API keys to GitHub.
- All sensitive values must be stored in **Azure Key Vault** or **Container Apps secrets**.
- Resource names used below are placeholders.

## Prerequisites

- Azure CLI installed
- Docker installed
- Access to an Azure subscription
- Permissions to create resources (RG, ACR, Key Vault, Container Apps)

## 0) Authenticate with Azure

```sh
az login
```

## 1) Deploy infrastructure (no job)

This deployment creates:

- Azure Container Registry (admin disabled)
- Log Analytics Workspace
- Container Apps Environment
- User-assigned Managed Identity
  - `AcrPull` on ACR
  - `Key Vault Secrets User` on Key Vault
- Key Vault
- Azure Maps
- Azure AI Foundry (keys stored in Key Vault)

```sh
az deployment group create \
  -g <RESOURCE_GROUP> \
  -f main.bicep \
  -p deployJob=false \
     acrName=<ACR_NAME>
```

## 2) Build & push the Docker image

Authentication uses Azure AD (ACR admin is disabled).

### Authenticate Docker

```sh
az acr login -n <ACR_NAME>
```

### Build & push image

```sh
docker build -t <IMAGE_REPO>:latest .
docker tag <IMAGE_REPO>:latest <ACR_NAME>.azurecr.io/<IMAGE_REPO>:latest
docker push <ACR_NAME>.azurecr.io/<IMAGE_REPO>:latest
```

## 3) Deploy the Container Apps Job

The job:
- Pulls the image from ACR using Managed Identity
- Reads secrets from Key Vault

```sh
az deployment group create \
  -g <RESOURCE_GROUP> \
  -f main.bicep \
  -p deployJob=true \
     acrName=<ACR_NAME> \
     imageRepo=<IMAGE_REPO> \
     imageTag=latest
```

## 4) Manual configuration

### 4.1 Azure AI Foundry
- Create a model deployment
- Collect endpoint, deployment name, and API key

### 4.2 Microsoft Teams webhook
- Create a Power Automate or Incoming Webhook
- Treat the webhook URL as a secret

### 4.3 Configure secrets in Azure Portal

Azure Portal → **Container Apps** → **Jobs** → select job

#### Configuration → Secrets
- `azure-openai-endpoint`
- `azure-openai-deployment-name`
- `azure-openai-api-key`
- `teams-webhook-url`

#### Containers → main → Environment variables
- `AZURE_OPENAI_ENDPOINT` → `azure-openai-endpoint`
- `AZURE_OPENAI_DEPLOYMENT_NAME` → `azure-openai-deployment-name`
- `AZURE_OPENAI_API_KEY` → `azure-openai-api-key`
- `TEAMS_WEBHOOK_URL` → `teams-webhook-url`

## 5) Sanity checks (optional)

### Show job

```sh
az containerapp job show \
  -g <RESOURCE_GROUP> \
  -n <JOB_NAME>
```

### List executions

```sh
az containerapp job execution list \
  -g <RESOURCE_GROUP> \
  --job-name <JOB_NAME>
```

### Trigger execution manually

```sh
az containerapp job start \
  -g <RESOURCE_GROUP> \
  -n <JOB_NAME>
```

## 6) Build a dev image

```sh
docker build --build-arg DEV=1 -t <IMAGE_REPO>:dev .
```

Behavior:
- If `.env` exists, it is copied to `/app/.env`
- If `.env` does not exist, nothing is copied