"""MCP server for Exchange email management via EWS."""

import logging
import os
import sys
from functools import partial
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .auth import AuthError, create_account
from .exchange import ExchangeClient

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("email_mcp")

MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))

# ── Initialize Exchange connection ───────────────────────────────

try:
    account = create_account()
    exchange = ExchangeClient(account)
except AuthError as e:
    logger.error("%s", e)
    sys.exit(1)

# exchangelib is synchronous — run blocking calls in a thread pool
_executor = ThreadPoolExecutor(max_workers=4)

mcp_server = FastMCP(
    "email-mcp",
    host=MCP_HOST,
    port=MCP_PORT,
)


async def _run_sync(func, *args, **kwargs):
    """Run a synchronous function in the thread pool."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, partial(func, *args, **kwargs))


# ── Formatting helpers ───────────────────────────────────────────


def _format_message_list(messages: list[dict]) -> str:
    if not messages:
        return "No emails found."

    lines = []
    for msg in messages:
        read_marker = "" if msg.get("is_read") else "[UNREAD] "
        attach = " [+attach]" if msg.get("has_attachments") else ""
        lines.append(
            f"{read_marker}{msg.get('date', '')[:16]}  "
            f"From: {msg.get('from', '')}\n"
            f"  To: {msg.get('to', '')}\n"
            f"  Subject: {msg.get('subject', '(no subject)')}{attach}\n"
            f"  Preview: {msg.get('preview', '')}\n"
            f"  ID: {msg.get('id', '')}"
        )
    return "\n\n".join(lines)


def _format_message_detail(msg: dict) -> str:
    parts = [
        f"Subject: {msg.get('subject', '(no subject)')}",
        f"From: {msg.get('from', '')}",
        f"To: {msg.get('to', '')}",
    ]
    if msg.get("cc"):
        parts.append(f"CC: {msg['cc']}")
    parts.extend([
        f"Date: {msg.get('date', '')}",
        f"Read: {msg.get('is_read', False)}",
        f"Has attachments: {msg.get('has_attachments', False)}",
        f"ID: {msg.get('id', '')}",
        "",
        "--- Body ---",
        msg.get("body", "(empty)"),
    ])
    return "\n".join(parts)


def _format_folders(folders: list[dict]) -> str:
    if not folders:
        return "No folders found."
    lines = []
    for f in folders:
        lines.append(
            f"{f.get('name', '?')} — "
            f"total: {f.get('total', 0)}, "
            f"unread: {f.get('unread', 0)}"
        )
    return "\n".join(lines)


def _format_attachments(attachments: list[dict]) -> str:
    if not attachments:
        return "No attachments."
    lines = []
    for a in attachments:
        size_kb = (a.get("size", 0) or 0) / 1024
        lines.append(f"- {a.get('name', '?')} ({a.get('content_type', '?')}, {size_kb:.1f} KB)")
    return "\n".join(lines)


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
        folder: Folder name — inbox, sent, drafts, trash, junk, or a custom folder name.
        count: Number of emails to return (max 50).
        skip: Number of emails to skip (for pagination).
        unread_only: If true, only return unread emails.
    """
    try:
        count = min(count, 50)
        messages = await _run_sync(
            exchange.list_messages, folder=folder, count=count, offset=skip, unread_only=unread_only
        )
        return _format_message_list(messages)
    except Exception as e:
        return f"Error: {e}"


@mcp_server.tool()
async def read_email(message_id: str) -> str:
    """Read the full content of a specific email by its ID.

    Args:
        message_id: The ID of the email message (from list_emails or search_emails).
    """
    try:
        msg = await _run_sync(exchange.get_message, message_id)
        return _format_message_detail(msg)
    except Exception as e:
        return f"Error: {e}"


@mcp_server.tool()
async def search_emails(query: str, count: int = 10) -> str:
    """Search emails by keywords in subject and body.

    Args:
        query: Search keywords.
        count: Number of results to return (max 50).
    """
    try:
        count = min(count, 50)
        messages = await _run_sync(exchange.search_messages, query, count)
        return _format_message_list(messages)
    except Exception as e:
        return f"Error: {e}"


# ── Sending emails ───────────────────────────────────────────────


@mcp_server.tool()
async def send_email(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
) -> str:
    """Send a new email.

    Args:
        to: Comma-separated recipient email addresses.
        subject: Email subject.
        body: Email body (HTML supported).
        cc: Comma-separated CC email addresses (optional).
    """
    try:
        to_list = [addr.strip() for addr in to.split(",") if addr.strip()]
        cc_list = [addr.strip() for addr in cc.split(",") if addr.strip()] if cc else None
        await _run_sync(exchange.send_message, subject, body, to_list, cc_list)
        return f"Email sent to {', '.join(to_list)}."
    except Exception as e:
        return f"Error: {e}"


@mcp_server.tool()
async def reply_to_email(
    message_id: str,
    body: str,
    reply_all: bool = False,
) -> str:
    """Reply to an email.

    Args:
        message_id: The ID of the email to reply to.
        body: The reply text.
        reply_all: If true, reply to all recipients.
    """
    try:
        await _run_sync(exchange.reply_to_message, message_id, body, reply_all)
        mode = "all recipients" if reply_all else "sender"
        return f"Reply sent to {mode}."
    except Exception as e:
        return f"Error: {e}"


@mcp_server.tool()
async def forward_email(
    message_id: str,
    to: str,
    body: str = "",
) -> str:
    """Forward an email to other recipients.

    Args:
        message_id: The ID of the email to forward.
        to: Comma-separated recipient email addresses.
        body: Optional message to include with the forwarded email.
    """
    try:
        to_list = [addr.strip() for addr in to.split(",") if addr.strip()]
        await _run_sync(exchange.forward_message, message_id, to_list, body)
        return f"Email forwarded to {', '.join(to_list)}."
    except Exception as e:
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
        await _run_sync(exchange.mark_as_read, message_id, is_read)
        status = "read" if is_read else "unread"
        return f"Email marked as {status}."
    except Exception as e:
        return f"Error: {e}"


@mcp_server.tool()
async def move_email(message_id: str, destination_folder: str) -> str:
    """Move an email to another folder.

    Args:
        message_id: The ID of the email to move.
        destination_folder: Destination folder name (inbox, trash, drafts, junk, etc.).
    """
    try:
        await _run_sync(exchange.move_message, message_id, destination_folder)
        return f"Email moved to {destination_folder}."
    except Exception as e:
        return f"Error: {e}"


@mcp_server.tool()
async def delete_email(message_id: str) -> str:
    """Permanently delete an email. This cannot be undone.

    To move to trash instead, use move_email with destination_folder='trash'.

    Args:
        message_id: The ID of the email to delete.
    """
    try:
        await _run_sync(exchange.delete_message, message_id)
        return "Email deleted permanently."
    except Exception as e:
        return f"Error: {e}"


# ── Folders & Attachments ────────────────────────────────────────


@mcp_server.tool()
async def list_folders() -> str:
    """List all mail folders with their message counts."""
    try:
        folders = await _run_sync(exchange.list_folders)
        return _format_folders(folders)
    except Exception as e:
        return f"Error: {e}"


@mcp_server.tool()
async def list_attachments(message_id: str) -> str:
    """List attachments of a specific email.

    Args:
        message_id: The ID of the email.
    """
    try:
        attachments = await _run_sync(exchange.list_attachments, message_id)
        return _format_attachments(attachments)
    except Exception as e:
        return f"Error: {e}"


# ── Entry point ──────────────────────────────────────────────────


def main():
    logger.info("Starting email-mcp server on %s:%s (SSE)", MCP_HOST, MCP_PORT)
    mcp_server.run(transport="sse")


if __name__ == "__main__":
    main()
