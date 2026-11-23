import os
import secrets
from functools import wraps
from urllib.parse import urlencode
import requests
import jwt
from jwt import PyJWKClient
from flask import Flask, redirect, request, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(24))

KC_EXTERNAL_URL = os.environ.get("KC_EXTERNAL_URL", "http://127.0.0.1:8180")
KC_INTERNAL_URL = os.environ.get("KC_INTERNAL_URL", "http://127.0.0.1:8180")
REALM = os.environ.get("KC_REALM", "pens-lab")
CLIENT_ID = os.environ.get("KC_CLIENT_ID", "flask-app")
CLIENT_SECRET = os.environ.get("KC_CLIENT_SECRET", "")
PORT = int(os.environ.get("FLASK_PORT", "5001"))
BASE_URL = os.environ.get("BASE_URL", f"http://127.0.0.1:{PORT}")
REDIRECT_URI = os.environ.get("REDIRECT_URI", f"{BASE_URL}/callback")

ISSUER = f"{KC_EXTERNAL_URL}/realms/{REALM}"
AUTH_URL = f"{KC_EXTERNAL_URL}/realms/{REALM}/protocol/openid-connect/auth"
TOKEN_URL = f"{KC_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/token"
LOGOUT_URL = f"{KC_EXTERNAL_URL}/realms/{REALM}/protocol/openid-connect/logout"
JWKS_URL = f"{KC_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/certs"

jwks_client = PyJWKClient(JWKS_URL)


def decode_and_verify_token(token: str) -> dict:
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=ISSUER,
        options={"verify_aud": False},
    )


def get_roles(claims: dict) -> set[str]:
    realm_roles = claims.get("realm_access", {}).get("roles", [])
    return set(realm_roles)


def require_role(required_role: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = session.get("access_token")
            if not token:
                return jsonify({"error": "unauthenticated", "detail": "Login required"}), 401
            try:
                claims = decode_and_verify_token(token)
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "token_expired"}), 401
            except jwt.InvalidTokenError as exc:
                return jsonify({"error": "invalid_token", "detail": str(exc)}), 401

            roles = get_roles(claims)
            if required_role not in roles:
                return jsonify({"error": "forbidden", "required_role": required_role, "roles": sorted(roles)}), 403

            request.user_claims = claims
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/")
def index():
    return jsonify({
        "status": "ok",
        "routes": ["/login", "/logout", "/profile", "/admin"],
    })


@app.route("/login")
def login():
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": REDIRECT_URI,
        "state": state,
    }
    return redirect(f"{AUTH_URL}?{urlencode(params)}")


@app.route("/callback")
def callback():
    if request.args.get("error"):
        return jsonify({"error": request.args.get("error"), "desc": request.args.get("error_description")}), 400

    state = request.args.get("state")
    if not state or state != session.pop("oauth_state", None):
        return jsonify({"error": "invalid_state"}), 400

    code = request.args.get("code")
    if not code:
        return jsonify({"error": "missing_code"}), 400

    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    if CLIENT_SECRET:
        payload["client_secret"] = CLIENT_SECRET

    resp = requests.post(TOKEN_URL, data=payload, timeout=10)
    if resp.status_code != 200:
        return jsonify({"error": "token_exchange_failed", "status": resp.status_code, "body": resp.text}), 401

    token_data = resp.json()
    session["access_token"] = token_data["access_token"]
    session["id_token"] = token_data.get("id_token")
    return redirect("/profile")


@app.route("/logout")
def logout():
    id_token = session.get("id_token")
    session.clear()

    params = {
        "client_id": CLIENT_ID,
        "post_logout_redirect_uri": f"{BASE_URL}/",
    }
    if id_token:
        params["id_token_hint"] = id_token

    return redirect(f"{LOGOUT_URL}?{urlencode(params)}")


@app.route("/profile")
@require_role("viewer")
def profile():
    claims = request.user_claims
    return jsonify({
        "sub": claims.get("sub"),
        "preferred_username": claims.get("preferred_username"),
        "roles": sorted(get_roles(claims)),
    })


@app.route("/admin")
@require_role("admin")
def admin_area():
    claims = request.user_claims
    return jsonify({
        "message": "Welcome to admin endpoint",
        "user": claims.get("preferred_username"),
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False)
