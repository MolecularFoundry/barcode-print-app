# barcode-print-app

Print Crucible sample barcode labels from anywhere, behind ORCID sign-in.

This is a standalone copy of the `/print` page from
[`sample-creators`](../sample-creators), for people who are not on the IP allowlist.
The on-site version stays where it is; the two apps are independent and may diverge.

Find samples in one of your Crucible projects (or paste/upload a list of MFIDs), build a
print list, and send the batch to a label printer over MQTT.

## Authentication

Sign-in is ORCID OAuth via `flask-pyoidc`, mirroring `crucible_graph_explorer`. After the
ORCID round trip, the app exchanges the ORCID iD for that user's own Crucible API key
(`POST /users/{orcid}/apikey`, using the admin key) and caches it in the session. Every
Crucible call the page makes then runs as the signed-in user, not as the admin.

An ORCID with no Crucible account is sent back to the sign-in page with a message — they
need to sign in at crucible.lbl.gov once to get an account.

## Local development

```
cp .env.example .env     # fill in ORCID credentials, CRUCIBLE_API_KEY, PYOIDC_SECRET
uv sync
uv run python app.py     # http://127.0.0.1:8000
```

`OIDC_REDIRECT_URI` must exactly match a redirect URI registered on the ORCID OAuth app,
including for local development (`http://127.0.0.1:8000/redirect_uri`).

## Deployment

Cloud Run, via `cloudbuild.yaml`. Set `_OIDC_REDIRECT_URI` (and `_URL_PREFIX` if the
service is mounted under a sub-path) as build substitutions; secrets come from Secret
Manager. `ProxyFix` is applied so the redirect URI is built as https behind Cloud Run.

## Printers

The printer allowlist lives in `config.py`. Users type the name of the printer they are
standing at — the list is deliberately not shown in the UI, and an unknown name is
rejected without enumerating the valid ones.
