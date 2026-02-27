"""MCP server for Microsoft 365 email management."""

import json
import logging
import os
import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .auth import AuthError, GraphAuth
from .graph import GraphAPIError, GraphClient

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("email_mcp")

# ── Configuration ────────────────────────────────────────────────

AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
TOKEN_PATH = os.getenv("TOKEN_PATH", ".tokens.json")
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))

if not all([AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID]):
    logger.error("Missing Azure credentials. Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID.")
    sys.exit(1)

auth = GraphAuth(AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, TOKEN_PATH)
graph = GraphClient(auth)

mcp_server = FastMCP(
    "email-mcp",
    host=MCP_HOST,
    port=MCP_PORT,
)


# ── Helper ───────────────────────────────────────────────────────


def _format_message_list(data: dict) -> str:
    messages = data.get("value", [])
    if not messages:
        return "No emails found."

    lines = []
    for msg in messages:
        sender = msg.get("from", {}).get("emailAddress", {})
        sender_str = f"{sender.get('name', '')} <{sender.get('address', '')}>".strip()
        read_marker = "" if msg.get("isRead") else "[UNREAD] "
        attach = " [+attach]" if msg.get("hasAttachments") else ""
        lines.append(
            f"{read_marker}{msg.get('receivedDateTime', '')[:16]}  "
            f"From: {sender_str}\n"
            f"  Subject: {msg.get('subject', '(no subject)')}{attach}\n"
            f"  Preview: {msg.get('bodyPreview', '')[:120]}\n"
            f"  ID: {msg.get('id', '')}"
        )
    return "\n\n".join(lines)


def _format_message_detail(msg: dict) -> str:
    sender = msg.get("from", {}).get("emailAddress", {})
    to_list = ", ".join(
        r.get("emailAddress", {}).get("address", "") for r in msg.get("toRecipients", [])
    )
    cc_list = ", ".join(
        r.get("emailAddress", {}).get("address", "") for r in msg.get("ccRecipients", [])
    )

    parts = [
        f"Subject: {msg.get('subject', '(no subject)')}",
        f"From: {sender.get('name', '')} <{sender.get('address', '')}>",
        f"To: {to_list}",
    ]
    if cc_list:
        parts.append(f"CC: {cc_list}")
    parts.extend([
        f"Date: {msg.get('receivedDateTime', '')}",
        f"Read: {msg.get('isRead', False)}",
        f"Has attachments: {msg.get('hasAttachments', False)}",
        f"ID: {msg.get('id', '')}",
        "",
        "--- Body ---",
        msg.get("body", {}).get("content", "(empty)"),
    ])
    return "\n".join(parts)


def _format_folders(data: dict) -> str:
    folders = data.get("value", [])
    if not folders:
        return "No folders found."
    lines = []
    for f in folders:
        lines.append(
            f"{f.get('displayName', '?')} — "
            f"total: {f.get('totalItemCount', 0)}, "
            f"unread: {f.get('unreadItemCount', 0)}, "
            f"ID: {f.get('id', '')}"
        )
    return "\n".join(lines)


def _format_attachments(data: dict) -> str:
    items = data.get("value", [])
    if not items:
        return "No attachments."
    lines = []
    for a in items:
        size_kb = (a.get("size", 0) or 0) / 1024
        lines.append(
            f"- {a.get('name', '?')} ({a.get('contentType', '?')}, {size_kb:.1f} KB)\n"
            f"  ID: {a.get('id', '')}"
        )
    return "\n".join(lines)


# ── Authentication tools ─────────────────────────────────────────


@mcp_server.tool()
async def authenticate() -> str:
    """Start the Microsoft 365 authentication flow.

    Returns a URL and code. The user must open the URL in a browser and enter the code.
    After authenticating, call check_auth_status to verify.
    """
    try:
        data = await auth.start_device_code_flow()
        device_code = data.get("device_code", "")
        message = data.get("message", "")

        # Start polling in background — will save tokens when done
        import asyncio
        interval = data.get("interval", 5)
        asyncio.create_task(auth.complete_device_code_flow(device_code, interval))

        return (
            f"Authentication started!\n\n{message}\n\n"
            "After completing the sign-in in your browser, "
            "call check_auth_status to verify the authentication succeeded."
        )
    except AuthError as e:
        return f"Authentication error: {e}"


@mcp_server.tool()
async def check_auth_status() -> str:
    """Check whether the server is authenticated with Microsoft 365."""
    if not auth.is_authenticated:
        return "Not authenticated. Use the 'authenticate' tool to log in."
    try:
        await auth.get_token()
        return "Authenticated and token is valid."
    except AuthError as e:
        return f"Authentication issue: {e}"


# ── Email listing & reading ──────────────────────────────────────


@mcp_server.tool()
async def list_emails(
    folder: str = "inbox",
    count: int = 10,
    skip: int = 0,
    unread_only: bool = False,
) -> str:
    """List emails from a mailbox folder.

    Args:
        folder: Mail folder name — inbox, sentitems, drafts, deleteditems, junkemail, or a folder ID.
        count: Number of emails to return (max 50).
        skip: Number of emails to skip (for pagination).
        unread_only: If true, only return unread emails.
    """
    try:
        count = min(count, 50)
        filter_q = "isRead eq false" if unread_only else None
        data = await graph.list_messages(folder, top=count, skip=skip, filter_query=filter_q)
        return _format_message_list(data)
    except (AuthError, GraphAPIError) as e:
        return f"Error: {e}"


@mcp_server.tool()
async def read_email(message_id: str) -> str:
    """Read the full content of a specific email by its ID.

    Args:
        message_id: The ID of the email message (from list_emails or search_emails).
    """
    try:
        msg = await graph.get_message(message_id)
        return _format_message_detail(msg)
    except (AuthError, GraphAPIError) as e:
        return f"Error: {e}"


@mcp_server.tool()
async def search_emails(query: str, count: int = 10) -> str:
    """Search emails by keywords across subject, body, sender, etc.

    Uses Microsoft Search (KQL). Examples:
    - "budget report" — search everywhere
    - "from:john@example.com" — emails from a specific person
    - "subject:meeting" — search in subject only
    - "hasAttachments:true project" — emails with attachments about "project"

    Args:
        query: Search query string (supports KQL syntax).
        count: Number of results to return (max 50).
    """
    try:
        count = min(count, 50)
        data = await graph.search_messages(query, top=count)
        return _format_message_list(data)
    except (AuthError, GraphAPIError) as e:
        return f"Error: {e}"


# ── Sending emails ───────────────────────────────────────────────


@mcp_server.tool()
async def send_email(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    is_html: bool = False,
) -> str:
    """Send a new email.

    Args:
        to: Comma-separated recipient email addresses.
        subject: Email subject.
        body: Email body text.
        cc: Comma-separated CC email addresses (optional).
        is_html: Whether the body is HTML (default: plain text).
    """
    try:
        to_list = [addr.strip() for addr in to.split(",") if addr.strip()]
        cc_list = [addr.strip() for addr in cc.split(",") if addr.strip()] if cc else None
        content_type = "HTML" if is_html else "Text"
        await graph.send_message(subject, body, to_list, cc_list, content_type)
        return f"Email sent to {', '.join(to_list)}."
    except (AuthError, GraphAPIError) as e:
        return f"Error: {e}"


@mcp_server.tool()
async def reply_to_email(
    message_id: str,
    comment: str,
    reply_all: bool = False,
) -> str:
    """Reply to an email.

    Args:
        message_id: The ID of the email to reply to.
        comment: The reply text.
        reply_all: If true, reply to all recipients.
    """
    try:
        await graph.reply_to_message(message_id, comment, reply_all)
        mode = "all recipients" if reply_all else "sender"
        return f"Reply sent to {mode}."
    except (AuthError, GraphAPIError) as e:
        return f"Error: {e}"


@mcp_server.tool()
async def forward_email(
    message_id: str,
    to: str,
    comment: str = "",
) -> str:
    """Forward an email to other recipients.

    Args:
        message_id: The ID of the email to forward.
        to: Comma-separated recipient email addresses.
        comment: Optional message to include with the forwarded email.
    """
    try:
        to_list = [addr.strip() for addr in to.split(",") if addr.strip()]
        await graph.forward_message(message_id, to_list, comment)
        return f"Email forwarded to {', '.join(to_list)}."
    except (AuthError, GraphAPIError) as e:
        return f"Error: {e}"


# ── Email management ─────────────────────────────────────────────


@mcp_server.tool()
async def mark_email(message_id: str, is_read: bool) -> str:
    """Mark an email as read or unread.

    Args:
        message_id: The ID of the email.
        is_read: True to mark as read, False to mark as unread.
    """
    try:
        await graph.update_message(message_id, isRead=is_read)
        status = "read" if is_read else "unread"
        return f"Email marked as {status}."
    except (AuthError, GraphAPIError) as e:
        return f"Error: {e}"


@mcp_server.tool()
async def move_email(message_id: str, destination_folder: str) -> str:
    """Move an email to another folder.

    Args:
        message_id: The ID of the email to move.
        destination_folder: Destination folder name (inbox, deleteditems, archive, junkemail) or folder ID.
    """
    try:
        await graph.move_message(message_id, destination_folder)
        return f"Email moved to {destination_folder}."
    except (AuthError, GraphAPIError) as e:
        return f"Error: {e}"


@mcp_server.tool()
async def delete_email(message_id: str) -> str:
    """Permanently delete an email. This cannot be undone.

    To move to trash instead, use move_email with destination_folder='deleteditems'.

    Args:
        message_id: The ID of the email to delete.
    """
    try:
        await graph.delete_message(message_id)
        return "Email deleted permanently."
    except (AuthError, GraphAPIError) as e:
        return f"Error: {e}"


# ── Folders & Attachments ────────────────────────────────────────


@mcp_server.tool()
async def list_folders() -> str:
    """List all mail folders with their message counts."""
    try:
        data = await graph.list_folders()
        return _format_folders(data)
    except (AuthError, GraphAPIError) as e:
        return f"Error: {e}"


@mcp_server.tool()
async def list_attachments(message_id: str) -> str:
    """List attachments of a specific email.

    Args:
        message_id: The ID of the email.
    """
    try:
        data = await graph.list_attachments(message_id)
        return _format_attachments(data)
    except (AuthError, GraphAPIError) as e:
        return f"Error: {e}"


# ── Entry point ──────────────────────────────────────────────────


def main():
    logger.info("Starting email-mcp server on %s:%s (SSE)", MCP_HOST, MCP_PORT)
    mcp_server.run(transport="sse")


if __name__ == "__main__":
    main()
