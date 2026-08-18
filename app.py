import logging
import os

import flask
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
from flask_pyoidc import OIDCAuthentication
from flask_pyoidc.provider_configuration import ClientMetadata, ProviderConfiguration
from flask_pyoidc.redirect_uri_config import RedirectUriConfig
from flask_pyoidc.user_session import UserSession
from werkzeug.middleware.proxy_fix import ProxyFix

from auth import fetch_user_api_key, get_user_client
from routes.print import print_bp

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)


class PrefixMiddleware:
    """Mount the app under a URL path prefix behind a reverse proxy.

    Sets SCRIPT_NAME so url_for() generates prefixed URLs, and strips the prefix from
    PATH_INFO when the proxy passes it through. A no-op when URL_PREFIX is unset, so
    local dev still serves at /.
    """

    def __init__(self, wsgi_app, prefix=""):
        self.wsgi_app = wsgi_app
        self.prefix = "/" + prefix.strip("/") if prefix.strip("/") else ""

    def __call__(self, environ, start_response):
        if not self.prefix:
            return self.wsgi_app(environ, start_response)

        environ["SCRIPT_NAME"] = self.prefix
        path = environ.get("PATH_INFO", "")
        if path.startswith(self.prefix):
            environ["PATH_INFO"] = path[len(self.prefix):] or "/"

        # flask-pyoidc redirects to request.full_path, which lacks SCRIPT_NAME;
        # re-add the prefix to internal-absolute redirect targets so the proxy can route them.
        def _fixup_start_response(status, headers, exc_info=None):
            if status.startswith("3"):
                headers = [
                    (k, self.prefix + v if k.lower() == "location"
                        and v.startswith("/") and not v.startswith("//")
                        and not v.startswith(self.prefix + "/") and v != self.prefix
                        else v)
                    for k, v in headers
                ]
            return start_response(status, headers, exc_info)

        return self.wsgi_app(environ, _fixup_start_response)


# Honor X-Forwarded-Proto/Host from Cloud Run so the redirect URI is https;
# PrefixMiddleware owns the path prefix.
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.wsgi_app = PrefixMiddleware(app.wsgi_app, os.environ.get("URL_PREFIX", ""))

app.secret_key = os.environ.get("PYOIDC_SECRET")

PROVIDER_CONFIG = ProviderConfiguration(
    issuer="https://orcid.org/",
    client_metadata=ClientMetadata(
        client_id=os.environ.get("ORCID_CLIENT_ID"),
        client_secret=os.environ.get("ORCID_CLIENT_SECRET"),
    ),
)
# Register the redirect route at the internal endpoint `/redirect_uri` (matched after
# SCRIPT_NAME stripping) while sending the full external URI — which may include the
# URL prefix — to ORCID. Default parsing would register the route at the full path.
oidc = OIDCAuthentication(
    {"orcid": PROVIDER_CONFIG},
    app,
    redirect_uri_config=RedirectUriConfig(os.environ.get("OIDC_REDIRECT_URI"), "redirect_uri"),
)

app.register_blueprint(print_bp)

_LOGIN_EXEMPT = {"/login", "/login/go", "/redirect_uri"}

NO_ACCOUNT_MESSAGE = (
    "That ORCID iD is not registered with Crucible. Sign in at crucible.lbl.gov to "
    "create an account, then come back."
)


def _build_session_user():
    """Cache the signed-in user's name and project list in the session."""
    userinfo = UserSession(flask.session).userinfo
    orcid = userinfo["sub"]
    given, family = userinfo.get("given_name", ""), userinfo.get("family_name", "")
    projects = sorted(
        p["project_id"]
        for p in get_user_client().projects.list(orcid=orcid, limit=int(1e5))
    )
    flask.session["user"] = {
        "user_name": f"{given}_{family}".strip("_") or orcid,
        "orcid": orcid,
        "projects": projects,
        "selected_project": projects[0] if projects else "",
    }


@app.before_request
def require_login():
    path = request.path
    if path.startswith("/static/") or path in _LOGIN_EXEMPT:
        return
    try:
        if UserSession(flask.session).userinfo and flask.session.get("user"):
            return
    except Exception:
        pass
    return redirect(url_for("login"))


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login/go")
@oidc.oidc_auth("orcid")
def login_go():
    if not fetch_user_api_key():
        flask.session.clear()
        return render_template("login.html", error=NO_ACCOUNT_MESSAGE)
    _build_session_user()
    return redirect(request.script_root + "/")


@app.route("/logout")
def logout():
    UserSession(flask.session).clear()
    flask.session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
