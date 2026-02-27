"""OAuth2 authentication for Microsoft Graph API.

Supports device code flow for initial auth and automatic token refresh.
"""

import json
import time
import asyncio
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

AUTHORITY = "https://login.microsoftonline.com"
GRAPH_SCOPES = (
    "https://graph.microsoft.com/Mail.ReadWrite "
    "https://graph.microsoft.com/Mail.Send "
    "offline_access"
)


class AuthError(Exception):
    pass


class GraphAuth:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        token_path: str = ".tokens.json",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.token_path = Path(token_path)
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.token_expiry: float = 0
        self._load_tokens()

    def _load_tokens(self) -> None:
        if self.token_path.exists():
            try:
                data = json.loads(self.token_path.read_text())
                self.refresh_token = data.get("refresh_token")
                self.access_token = data.get("access_token")
                self.token_expiry = data.get("token_expiry", 0)
                logger.info("Loaded saved tokens from %s", self.token_path)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load tokens: %s", e)

    def _save_tokens(self) -> None:
        self.token_path.write_text(
            json.dumps(
                {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "token_expiry": self.token_expiry,
                },
                indent=2,
            )
        )
        logger.info("Tokens saved to %s", self.token_path)

    @property
    def is_authenticated(self) -> bool:
        return self.refresh_token is not None

    @property
    def token_url(self) -> str:
        return f"{AUTHORITY}/{self.tenant_id}/oauth2/v2.0/token"

    @property
    def device_code_url(self) -> str:
        return f"{AUTHORITY}/{self.tenant_id}/oauth2/v2.0/devicecode"

    async def get_token(self) -> str:
        """Get a valid access token, refreshing if needed."""
        if self.access_token and time.time() < self.token_expiry - 60:
            return self.access_token

        if self.refresh_token:
            return await self._refresh_token()

        raise AuthError(
            "Not authenticated. Use the 'authenticate' tool to start the login flow."
        )

    async def _refresh_token(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                    "scope": GRAPH_SCOPES,
                },
            )
            data = resp.json()

        if "error" in data:
            self.access_token = None
            self.refresh_token = None
            self._save_tokens()
            raise AuthError(
                f"Token refresh failed ({data['error']}): {data.get('error_description', '')}. "
                "Please re-authenticate using the 'authenticate' tool."
            )

        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        self.token_expiry = time.time() + data.get("expires_in", 3600)
        self._save_tokens()
        return self.access_token

    async def start_device_code_flow(self) -> dict:
        """Start device code flow. Returns dict with user_code, verification_uri, etc."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.device_code_url,
                data={
                    "client_id": self.client_id,
                    "scope": GRAPH_SCOPES,
                },
            )
            data = resp.json()

        if "error" in data:
            raise AuthError(f"Device code request failed: {data}")

        return data

    async def complete_device_code_flow(
        self, device_code: str, interval: int = 5, timeout: int = 300
    ) -> bool:
        """Poll until user completes device code auth or timeout."""
        deadline = time.time() + timeout

        async with httpx.AsyncClient() as client:
            while time.time() < deadline:
                resp = await client.post(
                    self.token_url,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    },
                )
                data = resp.json()

                if "access_token" in data:
                    self.access_token = data["access_token"]
                    self.refresh_token = data.get("refresh_token")
                    self.token_expiry = time.time() + data.get("expires_in", 3600)
                    self._save_tokens()
                    return True

                error = data.get("error")
                if error == "authorization_pending":
                    await asyncio.sleep(interval)
                    continue
                elif error == "slow_down":
                    interval += 5
                    await asyncio.sleep(interval)
                    continue
                elif error == "expired_token":
                    raise AuthError("Device code expired. Please try again.")
                else:
                    raise AuthError(f"Authentication failed: {data}")

        raise AuthError("Authentication timed out. Please try again.")
