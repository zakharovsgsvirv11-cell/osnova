"""Microsoft Graph API client for email operations."""

import logging
from typing import Any

import httpx

from .auth import GraphAuth

logger = logging.getLogger(__name__)

BASE_URL = "https://graph.microsoft.com/v1.0"

MAX_BODY_LENGTH = 20_000


class GraphAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Graph API {status_code}: {message}")


class GraphClient:
    def __init__(self, auth: GraphAuth):
        self.auth = auth

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_body: dict | None = None,
        extra_headers: dict | None = None,
    ) -> dict | None:
        token = await self.auth.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        if extra_headers:
            headers.update(extra_headers)

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(
                method,
                f"{BASE_URL}{path}",
                headers=headers,
                params=params,
                json=json_body,
            )

        if resp.status_code >= 400:
            try:
                err = resp.json().get("error", {})
                msg = err.get("message", resp.text)
            except Exception:
                msg = resp.text
            raise GraphAPIError(resp.status_code, msg)

        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    # ── List / Read ──────────────────────────────────────────────

    async def list_messages(
        self,
        folder: str = "inbox",
        top: int = 10,
        skip: int = 0,
        filter_query: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {
            "$top": top,
            "$skip": skip,
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,from,toRecipients,receivedDateTime,isRead,hasAttachments,bodyPreview",
        }
        if filter_query:
            params["$filter"] = filter_query

        return await self._request("GET", f"/me/mailFolders/{folder}/messages", params=params)

    async def get_message(self, message_id: str) -> dict:
        msg = await self._request(
            "GET",
            f"/me/messages/{message_id}",
            extra_headers={"Prefer": 'outlook.body-content-type="text"'},
        )
        if msg and msg.get("body", {}).get("content"):
            body = msg["body"]["content"]
            if len(body) > MAX_BODY_LENGTH:
                msg["body"]["content"] = body[:MAX_BODY_LENGTH] + "\n\n[... truncated ...]"
        return msg

    async def search_messages(self, query: str, top: int = 10) -> dict:
        params: dict[str, Any] = {
            "$search": f'"{query}"',
            "$top": top,
            "$select": "id,subject,from,toRecipients,receivedDateTime,isRead,hasAttachments,bodyPreview",
            "$count": "true",
        }
        return await self._request(
            "GET",
            "/me/messages",
            params=params,
            extra_headers={"ConsistencyLevel": "eventual"},
        )

    # ── Send / Reply / Forward ───────────────────────────────────

    async def send_message(
        self,
        subject: str,
        body: str,
        to_recipients: list[str],
        cc_recipients: list[str] | None = None,
        content_type: str = "HTML",
    ) -> None:
        payload: dict[str, Any] = {
            "message": {
                "subject": subject,
                "body": {"contentType": content_type, "content": body},
                "toRecipients": [{"emailAddress": {"address": r}} for r in to_recipients],
            }
        }
        if cc_recipients:
            payload["message"]["ccRecipients"] = [
                {"emailAddress": {"address": r}} for r in cc_recipients
            ]
        await self._request("POST", "/me/sendMail", json_body=payload)

    async def reply_to_message(
        self, message_id: str, comment: str, reply_all: bool = False
    ) -> None:
        action = "replyAll" if reply_all else "reply"
        await self._request(
            "POST",
            f"/me/messages/{message_id}/{action}",
            json_body={"comment": comment},
        )

    async def forward_message(
        self, message_id: str, to_recipients: list[str], comment: str = ""
    ) -> None:
        await self._request(
            "POST",
            f"/me/messages/{message_id}/forward",
            json_body={
                "comment": comment,
                "toRecipients": [{"emailAddress": {"address": r}} for r in to_recipients],
            },
        )

    # ── Manage ───────────────────────────────────────────────────

    async def move_message(self, message_id: str, destination_folder_id: str) -> dict:
        return await self._request(
            "POST",
            f"/me/messages/{message_id}/move",
            json_body={"destinationId": destination_folder_id},
        )

    async def delete_message(self, message_id: str) -> None:
        await self._request("DELETE", f"/me/messages/{message_id}")

    async def update_message(self, message_id: str, **fields: Any) -> dict:
        return await self._request(
            "PATCH", f"/me/messages/{message_id}", json_body=fields
        )

    # ── Folders ──────────────────────────────────────────────────

    async def list_folders(self) -> dict:
        return await self._request(
            "GET",
            "/me/mailFolders",
            params={"$top": 100, "$select": "id,displayName,totalItemCount,unreadItemCount"},
        )

    # ── Attachments ──────────────────────────────────────────────

    async def list_attachments(self, message_id: str) -> dict:
        return await self._request(
            "GET",
            f"/me/messages/{message_id}/attachments",
            params={"$select": "id,name,contentType,size"},
        )
