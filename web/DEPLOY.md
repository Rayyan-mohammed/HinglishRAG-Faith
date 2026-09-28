# Deploying to AWS Lambda

Third hosting choice, after two dead ends: Hugging Face Spaces moved Docker Spaces behind a paid
plan, and Google Cloud Run required a ₹1000 account-verification prepayment in India before
billing would even activate. AWS Lambda has a genuinely perpetual free tier (1M requests +
400,000 GB-seconds compute/month, forever — not a 12-month trial) and only a ₹2 refundable
authorization hold to verify a card in India.

Local Docker Desktop also turned out to be unreliable on this machine (the engine hung mid-build
and needed a restart) — so this guide builds the image in **AWS CloudShell** instead, a
browser-based terminal built into the AWS Console with Docker pre-installed. Nothing to install
locally.

## Already done (for this account)

These exist already, no need to repeat them:
- ECR repository: `533047843280.dkr.ecr.us-east-1.amazonaws.com/codeswitch-verify`
- IAM execution role: `arn:aws:iam::533047843280:role/codeswitch-verify-lambda-role`
  (trust policy in `web/lambda-trust-policy.json`, has `AWSLambdaBasicExecutionRole` attached)

## 1. Open CloudShell

In the AWS Console (https://console.aws.amazon.com/), click the CloudShell icon in the top nav
bar (a `>_` icon). Wait for it to provision (~30-60s the first time).

## 2. Clone the repo and build the image

```bash
git clone https://github.com/Rayyan-mohammed/HinglishRAG-Faith.git
cd HinglishRAG-Faith/web
docker build -t codeswitch-verify-web .
```

CloudShell's environment is already `linux/amd64` (matches what Lambda needs), so no `--platform`
flag needed here, unlike building on Windows locally.

## 3. Push to ECR

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 533047843280.dkr.ecr.us-east-1.amazonaws.com
docker tag codeswitch-verify-web:latest 533047843280.dkr.ecr.us-east-1.amazonaws.com/codeswitch-verify:latest
docker push 533047843280.dkr.ecr.us-east-1.amazonaws.com/codeswitch-verify:latest
```

## 4. Create the Lambda function (first deploy only)

```bash
aws lambda create-function \
  --function-name codeswitch-verify \
  --package-type Image \
  --code ImageUri=533047843280.dkr.ecr.us-east-1.amazonaws.com/codeswitch-verify:latest \
  --role arn:aws:iam::533047843280:role/codeswitch-verify-lambda-role \
  --timeout 300 \
  --memory-size 4096 \
  --region us-east-1 \
  --environment "Variables={ANTHROPIC_API_KEY=your_actual_key_here}"
```

- `--timeout 300` — a `verify:true` request can take up to ~90s (majority-vote judging across
  several claims); this gives real headroom, well under Lambda's 900s (15 min) ceiling.
- `--memory-size 4096` — bge-m3 needs real RAM; Lambda also scales CPU proportionally with
  memory, which helps embedding speed too.
- `--environment` — Lambda environment variables are encrypted at rest by default, which is
  enough for a demo project; skip typing the real key in shell history by pasting it only when
  you run this command interactively, not by saving it in a script.

## 5. Make it publicly reachable (Function URL)

```bash
aws lambda create-function-url-config \
  --function-name codeswitch-verify \
  --auth-type NONE \
  --region us-east-1

aws lambda add-permission \
  --function-name codeswitch-verify \
  --statement-id FunctionURLAllowPublicAccess \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --function-url-auth-type NONE \
  --region us-east-1
```

The first command prints a `FunctionUrl` — that's the public site.

### 5b. If the Function URL answers "Forbidden" (new-account restriction) — use CloudFront

On a brand-new AWS account, anonymous access to a Function URL can be blocked. What worked here:
switch the URL to `AWS_IAM` auth and put CloudFront in front of it with an Origin Access Control
that signs requests to Lambda.

```bash
aws lambda update-function-url-config --function-name codeswitch-verify --auth-type AWS_IAM

aws cloudfront create-origin-access-control --origin-access-control-config \
  '{"Name":"codeswitch-verify-oac","SigningProtocol":"sigv4","SigningBehavior":"always","OriginAccessControlOriginType":"lambda"}'
# then create a distribution whose origin is the Function URL host, with that OAC id, all HTTP
# methods allowed, CachingDisabled policy, AllViewerExceptHostHeader origin policy, 60s read timeout.

aws lambda add-permission --function-name codeswitch-verify --statement-id cloudfront-invoke-url \
  --action lambda:InvokeFunctionUrl --principal cloudfront.amazonaws.com \
  --source-arn <distribution ARN> --function-url-auth-type AWS_IAM
aws lambda add-permission --function-name codeswitch-verify --statement-id cloudfront-invoke-fn \
  --action lambda:InvokeFunction --principal cloudfront.amazonaws.com --source-arn <distribution ARN>
```

The site is then served at the distribution's `*.cloudfront.net` address. A custom Route 53 domain
isn't possible on Free Tier accounts (domain registration is refused), so the cloudfront.net
address is the public URL. Because the URL is signed, `POST` bodies must carry their SHA-256 in
`x-amz-content-sha256` — the frontend does this in `App.jsx`.

## Memory: half-precision model

New accounts are capped at 3008MB of Lambda memory (concurrency limit 10 until AWS raises it), and
the stock fp32 bge-m3 runs out of memory there. `scripts/make_fp16_model.py` saves a half-precision
copy to `web/models/bge-m3-fp16` (not committed, ~1.1GB); the Dockerfile copies it in and sets
`EMBEDDING_MODEL` to it. Embeddings match fp32 to ~4 decimals with identical ranking. Run the
script once before building the image.

## Updating later

Rebuild, re-push, then point the function at the new image:

```bash
cd HinglishRAG-Faith && git pull && cd web
python scripts/make_fp16_model.py   # once, if web/models/ is missing
docker build --provenance=false -t codeswitch-verify-web .
docker tag codeswitch-verify-web:latest 533047843280.dkr.ecr.us-east-1.amazonaws.com/codeswitch-verify:latest
docker push 533047843280.dkr.ecr.us-east-1.amazonaws.com/codeswitch-verify:latest

aws lambda update-function-code \
  --function-name codeswitch-verify \
  --image-uri 533047843280.dkr.ecr.us-east-1.amazonaws.com/codeswitch-verify:latest \
  --region us-east-1
```

## Cold starts

No traffic means Lambda scales to zero (that's what keeps it free) — the first request after a
quiet period needs a fresh container: pull the image layers, load bge-m3, build the FAISS index,
*then* answer. This can take noticeably longer than Cloud Run's equivalent cold start, since
container-image Lambda cold starts are typically slower — possibly a minute or more on the very
first request. Subsequent requests to the same warm instance are fast. Eliminating this
(`--provisioned-concurrency`) costs money continuously instead of scaling to zero — a disclosed
tradeoff of staying on the free tier, not a bug.

## Rotate the AWS credentials used to set this up

The access key used to configure the CLI for this setup was shared in a chat at one point, which
means it should be treated as compromised regardless of who saw it. It's also a **root account**
key (unrestricted access, not a scoped IAM user). Once the deploy above is confirmed working:
delete that access key in the IAM console (or Root user → Security credentials), and if ongoing
CLI access is needed later, create a scoped IAM user instead of using root keys.
