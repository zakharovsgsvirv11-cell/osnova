"""Exchange Web Services client for email operations."""

import logging
from typing import Any

from exchangelib import (
    Account,
    FileAttachment,
    HTMLBody,
    Mailbox,
    Message,
)
from exchangelib.queryset import QuerySet

logger = logging.getLogger(__name__)

MAX_BODY_LENGTH = 20_000

# Mapping of friendly folder names to exchangelib account attributes
FOLDER_MAP = {
    "inbox": "inbox",
    "sent": "sent",
    "sentitems": "sent",
    "drafts": "drafts",
    "deleteditems": "trash",
    "trash": "trash",
    "junk": "junk",
    "junkemail": "junk",
    "outbox": "outbox",
}


class ExchangeClient:
    def __init__(self, account: Account):
        self.account = account

    def _get_folder(self, folder_name: str):
        """Resolve a folder name to an exchangelib folder object."""
        key = folder_name.lower().strip()
        attr = FOLDER_MAP.get(key)
        if attr:
            return getattr(self.account, attr)
        # Try to find by display name in all folders
        for f in self.account.root.walk():
            if f.name and f.name.lower() == key:
                return f
        raise ValueError(
            f"Folder '{folder_name}' not found. Use list_folders to see available folders."
        )

    @staticmethod
    def _format_address(mailbox: Mailbox | None) -> str:
        if not mailbox:
            return ""
        name = mailbox.name or ""
        addr = mailbox.email_address or ""
        if name and name != addr:
            return f"{name} <{addr}>"
        return addr

    # ── List / Read ──────────────────────────────────────────────

    def list_messages(
        self,
        folder: str = "inbox",
        count: int = 10,
        offset: int = 0,
        unread_only: bool = False,
    ) -> list[dict[str, Any]]:
        fld = self._get_folder(folder)
        qs: QuerySet = fld.all().order_by("-datetime_received")

        if unread_only:
            qs = fld.filter(is_read=False).order_by("-datetime_received")

        items = qs[offset : offset + count]
        results = []
        for msg in items:
            if not isinstance(msg, Message):
                continue
            results.append({
                "id": msg.id,
                "changekey": msg.changekey,
                "subject": msg.subject or "(no subject)",
                "from": self._format_address(msg.sender),
                "to": ", ".join(self._format_address(r) for r in (msg.to_recipients or [])),
                "date": str(msg.datetime_received or ""),
                "is_read": msg.is_read,
                "has_attachments": msg.has_attachments,
                "preview": (msg.text_body or "")[:150] if msg.text_body else "",
            })
        return results

    def get_message(self, message_id: str) -> dict[str, Any]:
        msg = self.account.inbox.get(id=message_id)
        if not isinstance(msg, Message):
            # Search across all default folders
            for folder_attr in ["inbox", "sent", "drafts", "trash", "junk"]:
                fld = getattr(self.account, folder_attr)
                try:
                    msg = fld.get(id=message_id)
                    if isinstance(msg, Message):
                        break
                except Exception:
                    continue
            else:
                raise ValueError(f"Message {message_id} not found.")

        body = msg.text_body or msg.body or ""
        if isinstance(body, HTMLBody):
            body = str(body)
        if len(body) > MAX_BODY_LENGTH:
            body = body[:MAX_BODY_LENGTH] + "\n\n[... truncated ...]"

        return {
            "id": msg.id,
            "subject": msg.subject or "(no subject)",
            "from": self._format_address(msg.sender),
            "to": ", ".join(self._format_address(r) for r in (msg.to_recipients or [])),
            "cc": ", ".join(self._format_address(r) for r in (msg.cc_recipients or [])),
            "date": str(msg.datetime_received or ""),
            "is_read": msg.is_read,
            "has_attachments": msg.has_attachments,
            "body": body,
        }

    def search_messages(self, query: str, count: int = 10) -> list[dict[str, Any]]:
        """Search in inbox by subject or body containing the query."""
        qs = (
            self.account.inbox
            .filter(body__contains=query)
            .order_by("-datetime_received")[:count]
        )
        results = []
        for msg in qs:
            if not isinstance(msg, Message):
                continue
            results.append({
                "id": msg.id,
                "subject": msg.subject or "(no subject)",
                "from": self._format_address(msg.sender),
                "to": ", ".join(self._format_address(r) for r in (msg.to_recipients or [])),
                "date": str(msg.datetime_received or ""),
                "is_read": msg.is_read,
                "has_attachments": msg.has_attachments,
                "preview": (msg.text_body or "")[:150] if msg.text_body else "",
            })
        return results

    # ── Send / Reply / Forward ───────────────────────────────────

    def send_message(
        self,
        subject: str,
        body: str,
        to_recipients: list[str],
        cc_recipients: list[str] | None = None,
    ) -> None:
        msg = Message(
            account=self.account,
            subject=subject,
            body=HTMLBody(body),
            to_recipients=[Mailbox(email_address=r) for r in to_recipients],
        )
        if cc_recipients:
            msg.cc_recipients = [Mailbox(email_address=r) for r in cc_recipients]
        msg.send()

    def reply_to_message(
        self, message_id: str, body: str, reply_all: bool = False
    ) -> None:
        msg = self._find_message(message_id)
        if reply_all:
            msg.reply_all(subject=f"Re: {msg.subject}", body=body)
        else:
            msg.reply(subject=f"Re: {msg.subject}", body=body)

    def forward_message(
        self, message_id: str, to_recipients: list[str], body: str = ""
    ) -> None:
        msg = self._find_message(message_id)
        msg.forward(
            subject=f"Fwd: {msg.subject}",
            body=body,
            to_recipients=[Mailbox(email_address=r) for r in to_recipients],
        )

    # ── Manage ───────────────────────────────────────────────────

    def move_message(self, message_id: str, destination_folder: str) -> None:
        msg = self._find_message(message_id)
        target = self._get_folder(destination_folder)
        msg.move(target)

    def delete_message(self, message_id: str) -> None:
        msg = self._find_message(message_id)
        msg.delete()

    def mark_as_read(self, message_id: str, is_read: bool = True) -> None:
        msg = self._find_message(message_id)
        msg.is_read = is_read
        msg.save(update_fields=["is_read"])

    # ── Folders ──────────────────────────────────────────────────

    def list_folders(self) -> list[dict[str, Any]]:
        results = []
        for f in self.account.root.walk():
            if f.name:
                results.append({
                    "name": f.name,
                    "total": f.total_count or 0,
                    "unread": f.unread_count or 0,
                    "id": f.id or "",
                })
        return results

    # ── Attachments ──────────────────────────────────────────────

    def list_attachments(self, message_id: str) -> list[dict[str, Any]]:
        msg = self._find_message(message_id)
        results = []
        for att in msg.attachments or []:
            info: dict[str, Any] = {
                "name": getattr(att, "name", "unknown"),
                "content_type": getattr(att, "content_type", "unknown"),
            }
            if isinstance(att, FileAttachment):
                info["size"] = att.size or 0
            results.append(info)
        return results

    # ── Internal ─────────────────────────────────────────────────

    def _find_message(self, message_id: str) -> Message:
        """Find a message by ID across common folders."""
        for folder_attr in ["inbox", "sent", "drafts", "trash", "junk", "outbox"]:
            fld = getattr(self.account, folder_attr, None)
            if fld is None:
                continue
            try:
                msg = fld.get(id=message_id)
                if isinstance(msg, Message):
                    return msg
            except Exception:
                continue
        raise ValueError(f"Message {message_id} not found in any folder.")
