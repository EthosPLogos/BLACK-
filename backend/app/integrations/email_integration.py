import email
import imaplib
import re
import smtplib
import ssl
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import (
    EMAIL_FOLDER,
    EMAIL_HOST,
    EMAIL_PASSWORD,
    EMAIL_PORT,
    EMAIL_SMTP_HOST,
    EMAIL_SMTP_PORT,
    EMAIL_USER,
)


def is_configured() -> bool:
    return bool(EMAIL_HOST and EMAIL_USER and EMAIL_PASSWORD)


def _decode_str(value, charset=None) -> str:
    if isinstance(value, bytes):
        try:
            return value.decode(charset or "utf-8", errors="replace")
        except Exception:
            return value.decode("latin-1", errors="replace")
    return value or ""


def _decode_header_value(header_value: str) -> str:
    if not header_value:
        return ""
    parts = decode_header(header_value)
    return "".join(
        _decode_str(part, charset) if isinstance(part, bytes) else (part or "")
        for part, charset in parts
    )


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    return re.sub(r"\s+", " ", text).strip()


def _get_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if ct == "text/plain" and "attachment" not in cd:
                charset = part.get_content_charset() or "utf-8"
                try:
                    return part.get_payload(decode=True).decode(charset, errors="replace")
                except Exception:
                    return ""
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                charset = part.get_content_charset() or "utf-8"
                try:
                    html = part.get_payload(decode=True).decode(charset, errors="replace")
                    return _strip_html(html)
                except Exception:
                    return ""
    else:
        charset = msg.get_content_charset() or "utf-8"
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                text = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/html":
                    return _strip_html(text)
                return text
        except Exception:
            pass
    return ""


def _connect() -> imaplib.IMAP4_SSL:
    ctx = ssl.create_default_context()
    conn = imaplib.IMAP4_SSL(EMAIL_HOST, int(EMAIL_PORT), ssl_context=ctx)
    conn.login(EMAIL_USER, EMAIL_PASSWORD)
    return conn


def _parse_message(conn, num) -> dict:
    # BODY.PEEK[] works with iCloud IMAP and does not mark messages as read
    _, data = conn.fetch(num, "(BODY.PEEK[])")
    # Filter to the tuple that holds actual bytes (iCloud appends a b')' element)
    raw = next((item[1] for item in data if isinstance(item, tuple) and isinstance(item[1], bytes)), None)
    if raw is None:
        return {"subject": "(unreadable)", "from": "", "date": "", "body": ""}
    msg = email.message_from_bytes(raw)
    return {
        "subject": _decode_header_value(msg.get("Subject", "(No subject)")),
        "from": _decode_header_value(msg.get("From", "")),
        "date": msg.get("Date", ""),
        "body": _get_body(msg)[:600].replace("\n", " ").strip(),
    }


def get_emails(limit: int = 10, unread_only: bool = False) -> list[dict]:
    if not is_configured():
        return []
    try:
        conn = _connect()
        conn.select(EMAIL_FOLDER)
        criteria = "UNSEEN" if unread_only else "ALL"
        _, msg_nums = conn.search(None, criteria)
        ids = msg_nums[0].split()
        recent = ids[-limit:][::-1]
        result = [_parse_message(conn, num) for num in recent]
        conn.logout()
        return result
    except Exception:
        return []


def get_unread_count() -> int:
    if not is_configured():
        return 0
    try:
        conn = _connect()
        conn.select(EMAIL_FOLDER)
        _, data = conn.search(None, "UNSEEN")
        count = len(data[0].split()) if data[0] else 0
        conn.logout()
        return count
    except Exception:
        return 0


def search_emails(query: str, limit: int = 10) -> list[dict]:
    if not is_configured():
        return []
    try:
        conn = _connect()
        conn.select(EMAIL_FOLDER)
        safe = query.replace('"', "").strip()
        _, by_subj = conn.search(None, f'SUBJECT "{safe}"')
        _, by_from = conn.search(None, f'FROM "{safe}"')
        ids = list({*by_subj[0].split(), *by_from[0].split()})
        recent = sorted(ids)[-limit:][::-1]
        result = [_parse_message(conn, num) for num in recent]
        conn.logout()
        return result
    except Exception:
        return []


def format_for_context(emails: list[dict]) -> str:
    if not emails:
        return "No emails found."
    lines = []
    for e in emails:
        lines.append(
            f"- From: {e['from']}\n"
            f"  Subject: {e['subject']}\n"
            f"  Date: {e['date']}\n"
            f"  Preview: {e['body'][:200]}"
        )
    return "\n".join(lines)


# ── Attachment parsing ─────────────────────────────────────────────────────────

def _get_attachments(msg) -> list[dict]:
    """Extract attachment metadata and raw bytes from a parsed email message."""
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            cd = str(part.get("Content-Disposition", ""))
            if "attachment" in cd:
                filename = part.get_filename() or "attachment"
                filename = _decode_header_value(filename)
                attachments.append({
                    "filename": filename,
                    "content_type": part.get_content_type(),
                    "data": part.get_payload(decode=True),
                })
    return attachments


def _parse_pdf(data: bytes) -> str:
    """Extract text from PDF bytes. Returns empty string if pypdf not installed."""
    try:
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages[:20]:  # cap at 20 pages
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return "\n\n".join(pages)
    except ImportError:
        return "[PDF parsing requires: pip install pypdf]"
    except Exception:
        return "[PDF could not be parsed]"


def _parse_docx(data: bytes) -> str:
    """Extract text from DOCX bytes. Returns empty string if python-docx not installed."""
    try:
        import io
        from docx import Document
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        return "[DOCX parsing requires: pip install python-docx]"
    except Exception:
        return "[DOCX could not be parsed]"


def get_email_with_attachments(uid: str) -> dict:
    """
    Fetch a single email by UID and parse any attachments.
    Returns message dict with 'attachments' list, each containing parsed text.
    """
    if not is_configured():
        return {}
    try:
        conn = _connect()
        conn.select(EMAIL_FOLDER)
        _, data = conn.fetch(uid.encode(), "(BODY.PEEK[])")
        raw = next((item[1] for item in data if isinstance(item, tuple) and isinstance(item[1], bytes)), None)
        if raw is None:
            return {}
        msg = email.message_from_bytes(raw)
        base = {
            "subject": _decode_header_value(msg.get("Subject", "(No subject)")),
            "from": _decode_header_value(msg.get("From", "")),
            "date": msg.get("Date", ""),
            "body": _get_body(msg),
            "attachments": [],
        }
        for att in _get_attachments(msg):
            ct = att["content_type"]
            text = ""
            if ct == "application/pdf":
                text = _parse_pdf(att["data"])
            elif ct in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "application/msword"):
                text = _parse_docx(att["data"])
            elif ct.startswith("text/"):
                text = att["data"].decode("utf-8", errors="replace") if att["data"] else ""
            base["attachments"].append({
                "filename": att["filename"],
                "content_type": ct,
                "text": text[:3000],  # cap per attachment
            })
        conn.logout()
        return base
    except Exception:
        return {}


# ── SMTP sending ───────────────────────────────────────────────────────────────

def smtp_is_configured() -> bool:
    return bool(EMAIL_SMTP_HOST and EMAIL_USER and EMAIL_PASSWORD)


def send_email(to: str, subject: str, body: str, reply_to_message_id: str | None = None) -> dict:
    """
    Send an email via SMTP.

    THIS FUNCTION MUST ONLY BE CALLED AFTER EXPLICIT OWNER APPROVAL.
    The approval gate in the orchestrator is responsible for ensuring this.

    Returns {"success": bool, "error": str | None}
    """
    if not smtp_is_configured():
        return {"success": False, "error": "SMTP not configured (EMAIL_SMTP_HOST / EMAIL_USER / EMAIL_PASSWORD missing)"}

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = to
        msg["Subject"] = subject
        if reply_to_message_id:
            msg["In-Reply-To"] = reply_to_message_id
            msg["References"] = reply_to_message_id
        msg.attach(MIMEText(body, "plain", "utf-8"))

        ctx = ssl.create_default_context()
        with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, [to], msg.as_string())

        return {"success": True, "error": None}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
