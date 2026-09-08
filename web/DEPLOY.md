# Deploying to Hugging Face Spaces

One-time setup, then a one-line command to redeploy after that.

## 1. Create the Space

1. Go to https://huggingface.co/new-space (create a free account first if you don't have one).
2. Pick a name (e.g. `codeswitch-verify`).
3. **SDK: Docker**.
4. Visibility: Public (or Private if you'd rather).
5. Create it — you'll land on an empty Space with a git remote URL like:
   `https://huggingface.co/spaces/<your-username>/<space-name>`

## 2. Add the Space as a git remote (once, from the repo root)

```
git remote add space https://huggingface.co/spaces/<your-username>/<space-name>
```

## 3. Add your API key as a Space secret

In the Space's page: **Settings → Repository secrets → New secret**.
- Name: `ANTHROPIC_API_KEY`
- Value: your key

Never commit this — it only lives in the Space's secret store.

## 4. Push

From the repo root:

```
git subtree push --prefix=web space main
```

This pushes only what's under `web/` as the Space's entire repository (so `web/Dockerfile` and
`web/README.md` land at the Space's root, which is what Hugging Face expects).

The Space will start building automatically — watch progress under the Space's **Logs** tab. The
first build takes a few minutes (installing dependencies, then downloading the bge-m3 embedding
model on first startup). Once it's live, the Space's URL
(`https://huggingface.co/spaces/<your-username>/<space-name>`) is the public site.

## Updating later

Edit files under `web/`, commit normally to the main repo (`git add web/... && git commit`), then
re-run:

```
git subtree push --prefix=web space main
```

That's the only command needed to redeploy.

## If `git subtree push` complains about a diverged/rejected push

This can happen if the Space already has commits it made itself (rare for Docker Spaces, but
possible). If so:

```
git push space `git subtree split --prefix=web main`:main --force
```

Use `--force` here deliberately and only for this — it's pushing your local `web/` state as the
new truth for the Space, which is what you want when redeploying from the main repo.
