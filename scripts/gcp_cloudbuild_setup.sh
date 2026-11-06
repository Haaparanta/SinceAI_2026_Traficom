#!/usr/bin/env bash
# One-time setup for deploys through Cloud Build (docs/HOSTING.md). Run after scripts/gcp_setup.sh.
# Safe to re-run. Step 3 prints a GitHub authorisation link the first time: open it, approve, then re-run.
#
#   scripts/gcp_cloudbuild_setup.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-filing-radar-513921}"
REGION="${REGION:-europe-north1}"
GH_REPO_URL="${GH_REPO_URL:-https://github.com/Haaparanta/SinceAI_2026_Traficom.git}"
CONN=github
REPO=filing-radar
TRIGGER=deploy-main
BUILD_SA="cloud-build-deploy@${PROJECT_ID}.iam.gserviceaccount.com"
RUN_SA="filing-radar-run@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project "$PROJECT_ID" >/dev/null
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
CB_AGENT="service-${PROJECT_NUMBER}@gcp-sa-cloudbuild.iam.gserviceaccount.com"

echo "== 1. APIs"
gcloud services enable cloudbuild.googleapis.com secretmanager.googleapis.com

echo "== 2. build service account: deploy to Cloud Run, push images, write build logs"
gcloud iam service-accounts describe "$BUILD_SA" >/dev/null 2>&1 ||
  { gcloud iam service-accounts create cloud-build-deploy --display-name="Cloud Build deploy"; sleep 10; }
for role in roles/run.admin roles/artifactregistry.writer roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member "serviceAccount:$BUILD_SA" --role "$role" \
    --condition=None --quiet >/dev/null
done
gcloud iam service-accounts add-iam-policy-binding "$RUN_SA" --member "serviceAccount:$BUILD_SA" \
  --role roles/iam.serviceAccountUser --quiet >/dev/null
# the Cloud Build service agent stores the GitHub token of the connection in Secret Manager
gcloud beta services identity create --service=cloudbuild.googleapis.com >/dev/null
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member "serviceAccount:$CB_AGENT" \
  --role roles/secretmanager.admin --condition=None --quiet >/dev/null

echo "== 3. GitHub connection"
gcloud builds connections describe "$CONN" --region "$REGION" >/dev/null 2>&1 ||
  gcloud builds connections create github "$CONN" --region "$REGION"
STAGE="$(gcloud builds connections describe "$CONN" --region "$REGION" --format='value(installationState.stage)')"
if [ "$STAGE" != "COMPLETE" ]; then
  echo
  echo "Open this link, sign in to GitHub, install the Cloud Build app on the repository, then re-run this script:"
  gcloud builds connections describe "$CONN" --region "$REGION" --format='value(installationState.actionUri)'
  exit 0
fi

echo "== 4. repository and trigger"
gcloud builds repositories describe "$REPO" --connection "$CONN" --region "$REGION" >/dev/null 2>&1 ||
  gcloud builds repositories create "$REPO" --connection "$CONN" --region "$REGION" --remote-uri "$GH_REPO_URL"
gcloud builds triggers describe "$TRIGGER" --region "$REGION" >/dev/null 2>&1 ||
  gcloud builds triggers create github --name "$TRIGGER" --region "$REGION" \
    --repository "projects/${PROJECT_ID}/locations/${REGION}/connections/${CONN}/repositories/${REPO}" \
    --branch-pattern '^main$' --build-config cloudbuild.yaml \
    --service-account "projects/${PROJECT_ID}/serviceAccounts/${BUILD_SA}"

echo "done. Run it now: gcloud builds triggers run ${TRIGGER} --region ${REGION} --branch main"
