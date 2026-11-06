# Hosted demo: Cloud Run + filingradar.click

The demo runs as one container on Google Cloud Run in `europe-north1` (Hamina, Finland): FastAPI under `/api`,
the built screen at `/`. It serves the committed analysis cache (`data/cache/`) and `results/` with
`DEMO_MODE=1` and `LLM_DISABLED=1`, so it needs no ITU databases, no network and no API key.

| Item | Value |
|---|---|
| Google Cloud project | `filing-radar-513921` |
| Region | `europe-north1` |
| Cloud Run service | `filing-radar` (1 vCPU, 512 MiB, min 1 / max 2 instances) |
| Images | `europe-north1-docker.pkg.dev/filing-radar-513921/filing-radar/app` |
| Domain | `filingradar.click` (Porkbun, auto-renew off) |
| Deploy | Cloud Build trigger `deploy-main` (`cloudbuild.yaml`) on every push to `main`; `.github/workflows/deploy.yml` by hand as a fallback |
| Checks | `.github/workflows/ci.yml` on every pull request |
| Budget | 3 EUR alert on the billing account |

## How a deploy works

Merge to `main` -> the Cloud Build trigger `deploy-main` (region `europe-north1`) runs `cloudbuild.yaml`: `pytest`,
build the `Dockerfile`, push it to Artifact Registry, deploy it to Cloud Run as `filing-radar-run`, then call `/health`
and `/api/issues`. It runs on Google's side, so it works even when GitHub Actions is unavailable. Builds and logs:
Cloud console -> Cloud Build -> History (region `europe-north1`), or `gcloud builds list --region europe-north1`.

`.github/workflows/deploy.yml` does the same from GitHub Actions, but only when started by hand, so a commit is never
deployed twice. Its Google sign-in uses Workload Identity Federation: no key is stored in GitHub, and the pool only
accepts tokens from this repository's `main` branch.

## Checks on every pull request

`.github/workflows/ci.yml` runs on every pull request and push to `main`: backend `pytest`, frontend lint and build,
`actionlint` over the workflows, and a build and smoke test of the deploy image. It never touches Google Cloud.

## Run the image locally

```bash
docker build -t filing-radar .
docker run --rm -p 8080:8080 filing-radar
```

Then open http://localhost:8080.

## One-time setup (already done once)

1. `gcloud auth login`
2. `scripts/gcp_setup.sh`: APIs, Artifact Registry, the runtime and deploy service accounts, the GitHub identity pool.
3. `scripts/gcp_cloudbuild_setup.sh`: the Cloud Build service account, the GitHub connection (it prints a link to
   install the Cloud Build GitHub app the first time; approve it and run the script again), the repository and the
   `deploy-main` trigger.
4. Push to `main`, or `gcloud builds triggers run deploy-main --region europe-north1 --branch main`, for the first deploy.
5. Custom domain (the domain must be verified in Search Console by the same Google account):
   `gcloud beta run domain-mappings create --service filing-radar --domain filingradar.click --region europe-north1`,
   then put the A and AAAA records it prints into Porkbun DNS. The certificate is issued automatically (15-60 min).

## Shut down after the event (Sunday 16:00)

Stop the always-on instance; the service then costs nothing while idle:

```bash
gcloud run services update filing-radar --region europe-north1 --min-instances 0
```

Or remove everything, which stops every charge:

```bash
gcloud projects delete filing-radar-513921
```
