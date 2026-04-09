import hashlib
import os
import base64
import urllib.parse
from typing import Optional
import httpx
from app.config import settings

X_AUTH_URL = "https://twitter.com/i/oauth2/authorize"
X_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
X_SCOPES = "tweet.read tweet.write users.read offline.access"


def _generate_code_verifier() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode()


def _generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def get_x_oauth_url(state: str) -> tuple[str, str]:
    verifier = _generate_code_verifier()
    challenge = _generate_code_challenge(verifier)
    params = {
        "response_type": "code",
        "client_id": settings.X_CLIENT_ID,
        "redirect_uri": settings.X_REDIRECT_URI,
        "scope": X_SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    url = f"{X_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return url, verifier


async def exchange_x_code(code: str, code_verifier: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            X_TOKEN_URL,
            data={
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.X_REDIRECT_URI,
                "code_verifier": code_verifier,
            },
            auth=(settings.X_CLIENT_ID, settings.X_CLIENT_SECRET),
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_x_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            X_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            auth=(settings.X_CLIENT_ID, settings.X_CLIENT_SECRET),
        )
        resp.raise_for_status()
        return resp.json()
