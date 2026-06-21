from __future__ import annotations

import email
import imaplib
import re
from email.header import decode_header, make_header

from .models import Email


def _decode_header(value: str | None) -> str:
    if value is None:
        return ""
    return str(make_header(decode_header(value)))


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def _decode_payload(part) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def _extract_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            disp = str(part.get("Content-Disposition"))
            if part.get_content_type() == "text/plain" and "attachment" not in disp:
                text = _decode_payload(part)
                if text:
                    return text
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return _strip_html(_decode_payload(part))
        return ""
    text = _decode_payload(msg)
    if msg.get_content_type() == "text/html":
        return _strip_html(text)
    return text


def parse_email_message(raw: bytes, index: int) -> Email:
    msg = email.message_from_bytes(raw)
    return Email(
        index=index,
        sender=_decode_header(msg.get("From")),
        subject=_decode_header(msg.get("Subject")),
        date=_decode_header(msg.get("Date")),
        body=_extract_body(msg).strip(),
    )


class MailReader:
    def __init__(self, host: str, port: int, email_addr: str, password: str):
        self.host = host
        self.port = port
        self.email_addr = email_addr
        self.password = password

    def fetch_recent(self, count: int) -> list[Email]:
        conn = imaplib.IMAP4_SSL(self.host, self.port)
        try:
            conn.login(self.email_addr, self.password)
            conn.select("INBOX")
            _typ, data = conn.search(None, "ALL")
            ids = data[0].split()
            recent = ids[-count:][::-1]  # newest first
            emails: list[Email] = []
            for i, msg_id in enumerate(recent, start=1):
                _typ, msg_data = conn.fetch(msg_id, "(RFC822)")
                raw = msg_data[0][1]
                emails.append(parse_email_message(raw, i))
            return emails
        finally:
            try:
                conn.logout()
            except Exception:
                pass
