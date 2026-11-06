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
| Deploy | `.github/workflows/deploy.yml` on every push to `main` |
| Budget | 3 EUR alert on the billing account |

## How a deploy works

Merge to `main` -> GitHub Actions runs `pytest`, builds the `Dockerfile`, pushes it to Artifact Registry and deploys
it to Cloud Run, then calls `/healthz` and `/api/issues`. Google sign-in uses Workload Identity Federation: no key is
stored in GitHub, and the pool only accepts tokens from this repository's `main` branch.

## Run the image locally

```bash
docker build -t filing-radar .
docker run --rm -p 8080:8080 filing-radar
```

Then open http://localhost:8080.

## One-time setup (already done once)

1. `gcloud auth login`
2. `scripts/gcp_setup.sh`: APIs, Artifact Registry, the runtime and deploy service accounts, the GitHub identity pool.
3. Push to `main` (or run the workflow by hand) for the first deploy.
4. Custom domain (the domain must be verified in Search Console by the same Google account):
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
