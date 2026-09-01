import logging
import os

import flask
from crucible import CrucibleClient
from dotenv import load_dotenv
from flask_pyoidc.user_session import UserSession

# Module-level env reads below run at import time, so the .env has to be loaded first.
load_dotenv()

logger = logging.getLogger(__name__)

CRUCIBLE_API_URL = os.environ.get("CRUCIBLE_API_URL", "https://crucible.lbl.gov/api/v3")

# Only ever used to mint a user's personal API key. Every call made on behalf of a
# signed-in user goes through get_user_client() instead.
admin_client = CrucibleClient(
    api_url=CRUCIBLE_API_URL,
    api_key=os.environ.get("CRUCIBLE_API_KEY", ""),
)


def fetch_user_api_key():
    """Put the signed-in user's personal Crucible API key in the session.

    POST /users/{orcid}/apikey returns the user's key, minting one if they do not
    have it yet, and 404s when the ORCID has no Crucible account at all. Returns
    False in that case so the caller can tell the user to sign up.
    """
    if flask.session.get("crucible_apikey"):
        return True
    try:
        orcid = UserSession(flask.session).userinfo["sub"]
        key = (admin_client._request("POST", f"/users/{orcid}/apikey") or {}).get("api_key")
    except Exception as e:
        logger.warning("Could not fetch Crucible API key: %s", e)
        return False
    if not key:
        return False
    flask.session["crucible_apikey"] = key
    return True


def get_user_client():
    """Return a per-request CrucibleClient using the signed-in user's API key.

    Cached on flask.g so it is created at most once per request.
    Aborts with 401 if no key is present in the session.
    """
    if "user_client" not in flask.g:
        key = flask.session.get("crucible_apikey")
        if not key:
            flask.abort(401)
        flask.g.user_client = CrucibleClient(api_url=CRUCIBLE_API_URL, api_key=key)
    return flask.g.user_client
