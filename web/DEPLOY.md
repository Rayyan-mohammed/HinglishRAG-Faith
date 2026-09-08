# Deploying to Google Cloud Run

Switched from Hugging Face Spaces after HF moved Docker Spaces behind a paid plan (mid-2026).
Cloud Run has a genuine perpetual free tier (2M requests/month, scales to zero cost when idle)
and deploys straight from this `web/` folder — no git subtree tricks needed, unlike the HF
approach this replaced.

**One real cost to know about upfront:** Google requires a credit card on file for any Cloud
project, even to stay within the free tier. You won't be charged for usage that stays under the
free quota (which is generous for a low-traffic demo), but the card is a real requirement, not
optional.

## 1. One-time account setup

1. Go to https://console.cloud.google.com/ and sign in (free Google account is fine).
2. Create a new **Project** (top-left project picker → New Project). Note the Project ID.
3. You'll be prompted to link a **Billing account** — add a card. Again: this doesn't mean
   you're charged, it's required to enable any compute service including the free tier.
4. Install the `gcloud` CLI: https://cloud.google.com/sdk/docs/install (or use **Cloud Shell** in
   the browser console instead — it has `gcloud` preinstalled, no local install needed, and can
   run every command below directly from a browser terminal).
5. Authenticate and set your project:
   ```
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

## 2. Store the API key in Secret Manager (once)

Don't pass the key as a plain env var on the deploy command — it'd end up in shell history and
Cloud Build logs. Store it as a secret instead:

```
gcloud services enable secretmanager.googleapis.com run.googleapis.com cloudbuild.googleapis.com
echo -n "your-actual-anthropic-api-key" | gcloud secrets create anthropic-api-key --data-file=-
```

## 3. Deploy

From the repo root:

```
gcloud run deploy codeswitch-verify \
  --source ./web \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --set-secrets ANTHROPIC_API_KEY=anthropic-api-key:latest
```

What each flag is for:
- `--source ./web` — builds `web/Dockerfile` directly from this folder, no separate image push step.
- `--memory 4Gi` — bge-m3 needs real RAM; Cloud Run's 512MiB default is too small.
- `--timeout 300` — a `verify: true` request can take up to ~90s (majority-vote judging across
  several claims); the default request timeout is fine but this makes the headroom explicit.
- `--allow-unauthenticated` — makes the demo publicly reachable without requiring Google sign-in
  to use it (the app's own rate limiter is still the cost guard, not Google auth).

First deploy takes a few minutes (Cloud Build builds the multi-stage Docker image). When it
finishes, `gcloud` prints the live URL — that's the public site.

## Updating later

Same command, run again after making changes:

```
gcloud run deploy codeswitch-verify --source ./web --region us-central1
```
(Cloud Run remembers the previous flags like `--memory`/`--set-secrets` across revisions, so a
plain re-run usually doesn't need every flag repeated — but if something looks off after a
redeploy, re-run the full command from step 3 to be sure.)

## Cold starts

Cloud Run scales to zero when idle (that's what keeps it free) — the first request after a quiet
period triggers a fresh container start, which needs to download/load the bge-m3 embedding model
and build the FAISS index before it can answer (roughly 30-60s). Subsequent requests to the same
warm instance are fast. This is a real, disclosed tradeoff of staying on the free tier — setting
`--min-instances 1` would keep one instance always warm and eliminate this, at the cost of
ongoing charges instead of scale-to-zero.
