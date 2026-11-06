#!/usr/bin/env bash
# One-time Google Cloud setup for the hosted demo (docs/HOSTING.md). Safe to re-run: every step checks first.
# Needs: gcloud logged in as a project owner (gcloud auth login).
#
#   scripts/gcp_setup.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-filing-radar-513921}"
REGION="${REGION:-europe-north1}"
GH_REPO="${GH_REPO:-Haaparanta/SinceAI_2026_Traficom}"
AR_REPO=filing-radar
DEPLOY_SA="github-deploy@${PROJECT_ID}.iam.gserviceaccount.com"
RUN_SA="filing-radar-run@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project "$PROJECT_ID" >/dev/null
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
echo "project $PROJECT_ID ($PROJECT_NUMBER), region $REGION, repo $GH_REPO"

echo "== APIs"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com iam.googleapis.com \
  iamcredentials.googleapis.com sts.googleapis.com

echo "== Artifact Registry"
gcloud artifacts repositories describe "$AR_REPO" --location "$REGION" >/dev/null 2>&1 ||
  gcloud artifacts repositories create "$AR_REPO" --repository-format=docker --location "$REGION" \
    --description="Filing Radar demo images"

echo "== service accounts"
gcloud iam service-accounts describe "$RUN_SA" >/dev/null 2>&1 ||
  gcloud iam service-accounts create filing-radar-run --display-name="Filing Radar runtime (no roles)"
gcloud iam service-accounts describe "$DEPLOY_SA" >/dev/null 2>&1 ||
  gcloud iam service-accounts create github-deploy --display-name="GitHub Actions deploy"

for role in roles/run.admin roles/artifactregistry.writer; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member "serviceAccount:$DEPLOY_SA" --role "$role" \
    --condition=None --quiet >/dev/null
done
# the deployer may run the service as the runtime account, and only that one
gcloud iam service-accounts add-iam-policy-binding "$RUN_SA" --member "serviceAccount:$DEPLOY_SA" \
  --role roles/iam.serviceAccountUser --quiet >/dev/null

echo "== Workload Identity Federation (GitHub OIDC, this repository only)"
gcloud iam workload-identity-pools describe github --location global >/dev/null 2>&1 ||
  gcloud iam workload-identity-pools create github --location global --display-name="GitHub Actions"
gcloud iam workload-identity-pools providers describe github --workload-identity-pool github --location global >/dev/null 2>&1 ||
  gcloud iam workload-identity-pools providers create-oidc github --workload-identity-pool github --location global \
    --display-name="GitHub" --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
    --attribute-condition="assertion.repository == '${GH_REPO}' && assertion.ref == 'refs/heads/main'"
gcloud iam service-accounts add-iam-policy-binding "$DEPLOY_SA" --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github/attribute.repository/${GH_REPO}" \
  --quiet >/dev/null

echo "done. Workflow provider: projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github/providers/github"
