"""Load the Google credentials created in L05.

The private folder is read from the environment variable GOOGLE_PRIVATE_DIR.
Secrets are never copied into this project and never printed.
This module never opens a browser: if the token is missing or revoked,
it raises a clear error telling you to re-run the L05 program.
"""

import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

_cache: dict = {}


def _private_dir() -> str:
    path = os.environ.get("GOOGLE_PRIVATE_DIR", "").strip()
    if not path:
        raise RuntimeError("GOOGLE_PRIVATE_DIR is not set. "
                           "Point it to the folder that holds token.json.")
    if not os.path.isdir(path):
        raise RuntimeError(f"GOOGLE_PRIVATE_DIR must be a folder, got: {path}")
    return path


def get_credentials() -> Credentials:
    token_path = os.path.join(_private_dir(), "token.json")
    if not os.path.exists(token_path):
        raise RuntimeError("token.json not found in GOOGLE_PRIVATE_DIR. "
                           "Run the L05 test program once to create it.")
    # Keep whatever scopes L05 granted (no scopes argument = no new consent).
    creds = Credentials.from_authorized_user_file(token_path)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as exc:  # invalid_grant etc.
                raise RuntimeError("The Google token expired or was revoked "
                                   "(invalid_grant). Run the L05 program again "
                                   "to renew token.json.") from exc
            with open(token_path, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
        else:
            raise RuntimeError("token.json is not valid. Run the L05 program again.")
    return creds


def service(name: str, version: str):
    """Return a cached Google API client (gmail v1 / calendar v3)."""
    key = (name, version)
    if key not in _cache:
        _cache[key] = build(name, version, credentials=get_credentials(),
                            cache_discovery=False)
    return _cache[key]


def log(msg: str) -> None:
    """stdio servers must never write to stdout - log to stderr only."""
    print(msg, file=sys.stderr)
