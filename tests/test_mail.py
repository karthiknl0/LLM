from email.message import EmailMessage

import app.services.mail as mail


def test_unconfigured_returns_setup_message(monkeypatch):
    monkeypatch.delenv("AIHUB_IMAP_USER", raising=False)
    monkeypatch.delenv("AIHUB_IMAP_PASSWORD", raising=False)
    assert "not configured" in mail.search_email("anything")
    assert "not configured" in mail.read_email("1")
    assert mail.is_configured() is False


def test_read_email_requires_numeric_id(monkeypatch):
    monkeypatch.setenv("AIHUB_IMAP_USER", "a@b.c")
    monkeypatch.setenv("AIHUB_IMAP_PASSWORD", "x")
    assert "numeric email id" in mail.read_email("abc")


def test_decode_handles_encoded_headers():
    assert mail._decode("plain subject") == "plain subject"
    assert mail._decode("=?utf-8?q?caf=C3=A9?=") == "café"
    assert mail._decode(None) == ""


def test_body_plain_text():
    msg = EmailMessage()
    msg.set_content("hello body")
    assert "hello body" in mail._body(msg)


def test_body_multipart_prefers_plain():
    msg = EmailMessage()
    msg.set_content("plain version")
    msg.add_alternative("<p>html version</p>", subtype="html")
    assert "plain version" in mail._body(msg)


def test_body_html_only_strips_tags():
    msg = EmailMessage()
    msg.set_content("<p>only <b>html</b> here</p>", subtype="html")
    body = mail._body(msg)
    assert "html" in body and "<p>" not in body
