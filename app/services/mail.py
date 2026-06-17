"""Read-only email for the agent over IMAP: search and read your
inbox — never send, never delete (connections are opened read-only and
fetches use PEEK, so messages aren't even marked as read).

Setup (Gmail):
  1. Enable 2-Step Verification on your Google account.
  2. Create an App Password at myaccount.google.com/apppasswords
  3. Set env vars before starting the hub:
       AIHUB_IMAP_USER     = you@gmail.com
       AIHUB_IMAP_PASSWORD = <the 16-character app password>
       AIHUB_IMAP_HOST     = imap.gmail.com   (default)

Works with any IMAP provider. Outlook.com/Microsoft 365 no longer
allow IMAP passwords — use a Microsoft 365 MCP server instead (README).
"""

import email
import email.header
import imaplib
import os
import re

MAX_RESULTS = 10
MAX_BODY_CHARS = 3000


def _config():
    return (
        os.environ.get("AIHUB_IMAP_HOST", "imap.gmail.com"),
        os.environ.get("AIHUB_IMAP_USER"),
        os.environ.get("AIHUB_IMAP_PASSWORD"),
    )


def _connect():
    host, user, password = _config()
    if not (user and password):
        return None, (
            "Email is not configured. Set AIHUB_IMAP_USER and "
            "AIHUB_IMAP_PASSWORD (for Gmail: an App Password from "
            "myaccount.google.com/apppasswords) before starting the hub."
        )
    try:
        conn = imaplib.IMAP4_SSL(host)
        conn.login(user, password)
        conn.select("INBOX", readonly=True)
        return conn, None
    except Exception as exc:
        return None, f"Email connection failed: {exc}"


def _decode(value: str | None) -> str:
    out = ""
    for text, charset in email.header.decode_header(value or ""):
        if isinstance(text, bytes):
            out += text.decode(charset or "utf-8", "replace")
        else:
            out += text
    return out


def _body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if (
                part.get_content_type() == "text/plain"
                and not part.get("Content-Disposition")
            ):
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(
                        part.get_content_charset() or "utf-8", "replace"
                    )
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    html = payload.decode(
                        part.get_content_charset() or "utf-8", "replace"
                    )
                    return re.sub(r"<[^>]+>", " ", html)
        return "(no readable body)"
    payload = msg.get_payload(decode=True)
    if not payload:
        return "(empty)"
    text = payload.decode(msg.get_content_charset() or "utf-8", "replace")
    if msg.get_content_type() == "text/html":
        text = re.sub(r"<[^>]+>", " ", text)
    return text


def search_email(query: str = "") -> str:
    """Agent tool: list recent inbox emails, optionally matching a term."""
    conn, error = _connect()
    if error:
        return error
    try:
        if (query or "").strip():
            _typ, data = conn.search(None, "TEXT", f'"{query.strip()}"')
        else:
            _typ, data = conn.search(None, "ALL")
        ids = data[0].split()[-MAX_RESULTS:]
        if not ids:
            return "No matching emails found."
        lines = []
        for mid in reversed(ids):
            _typ, msgdata = conn.fetch(
                mid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])"
            )
            msg = email.message_from_bytes(msgdata[0][1])
            lines.append(
                f"- id {mid.decode()}: {_decode(msg['Subject'])} — "
                f"from {_decode(msg['From'])} ({msg['Date']})"
            )
        return (
            "Recent emails (newest first):\n" + "\n".join(lines)
            + "\n\nUse read_email with an id to read one."
        )
    finally:
        conn.logout()


def read_email(email_id: str) -> str:
    """Agent tool: read one email by the id shown in search_email."""
    if not (email_id or "").strip().isdigit():
        return "Provide a numeric email id from search_email."
    conn, error = _connect()
    if error:
        return error
    try:
        _typ, msgdata = conn.fetch(email_id.strip().encode(), "(BODY.PEEK[])")
        if not msgdata or msgdata[0] is None:
            return f"No email with id {email_id}."
        msg = email.message_from_bytes(msgdata[0][1])
        return (
            f"From: {_decode(msg['From'])}\n"
            f"Subject: {_decode(msg['Subject'])}\n"
            f"Date: {msg['Date']}\n\n"
            f"{_body(msg)[:MAX_BODY_CHARS]}"
        )
    finally:
        conn.logout()


def is_configured() -> bool:
    _host, user, password = _config()
    return bool(user and password)
