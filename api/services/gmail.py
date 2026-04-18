"""
Gmail Service -- Lecture (IMAP) et envoi (SMTP) de mails via App Password.

Utilise par le blueprint /api/gmail pour exposer les fonctionnalites
sans coupler directement Flask au protocole IMAP/SMTP.
"""

from __future__ import annotations

import email
import email.encoders
import imaplib
import json
import logging
import os
import re
import smtplib
from datetime import datetime, timedelta
from email.header import decode_header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from openai import OpenAI

logger = logging.getLogger(__name__)

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

CATEGORIES_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "gmail_categories.json"

VALID_STATUSES = {"Nouveau", "En cours", "Traite"}


class GmailService:
    """Service singleton for Gmail operations via IMAP/SMTP."""

    def __init__(self) -> None:
        self._imap: imaplib.IMAP4_SSL | None = None
        self._connected: bool = False

    # -- helpers ----------------------------------------------------------------

    @property
    def address(self) -> str:
        return os.getenv("GMAIL_ADDRESS", "")

    @property
    def app_password(self) -> str:
        return os.getenv("GMAIL_APP_PASSWORD", "")

    @property
    def available(self) -> bool:
        return bool(self.address and self.app_password)

    @property
    def connected(self) -> bool:
        return self._connected

    # -- connection -------------------------------------------------------------

    def connect(self) -> bool:
        """Test IMAP connection and authenticate."""
        try:
            imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
            imap.login(self.address, self.app_password)
            imap.logout()
            self._connected = True
            logger.info("Gmail connected for %s", self.address)
            return True
        except Exception as exc:
            logger.error("Gmail connection failed: %s", exc)
            self._connected = False
            return False

    def _get_imap(self) -> imaplib.IMAP4_SSL:
        """Return an authenticated IMAP connection (fresh each time)."""
        imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        imap.login(self.address, self.app_password)
        return imap

    # -- reading ----------------------------------------------------------------

    @staticmethod
    def _decode_header_value(raw: str) -> str:
        """Decode an RFC-2047 encoded header into a plain string."""
        parts = decode_header(raw)
        decoded = []
        for data, charset in parts:
            if isinstance(data, bytes):
                decoded.append(data.decode(charset or "utf-8", errors="replace"))
            else:
                decoded.append(data)
        return " ".join(decoded)

    @staticmethod
    def _extract_attachments(msg: email.message.Message) -> list[dict[str, Any]]:
        """Extract attachment metadata from a MIME message."""
        attachments: list[dict[str, Any]] = []
        part_index = 0
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            content_type = part.get_content_type()
            if "attachment" in content_disposition or (
                content_type not in ("text/plain", "text/html", "multipart/mixed",
                                     "multipart/alternative", "multipart/related")
                and part.get_payload(decode=True) is not None
                and "attachment" not in content_disposition
                and part.get_content_maintype() != "multipart"
                and part.get_filename()
            ):
                filename = part.get_filename() or f"attachment_{part_index}"
                if isinstance(filename, bytes):
                    filename = filename.decode("utf-8", errors="replace")
                else:
                    filename = GmailService._decode_header_value(filename)
                payload = part.get_payload(decode=True)
                size = len(payload) if payload else 0
                attachments.append({
                    "filename": filename,
                    "content_type": content_type,
                    "size": size,
                    "part_index": part_index,
                })
            part_index += 1
        return attachments

    @staticmethod
    def _sanitize_for_llm(text: str) -> str:
        """Sanitize email text to mitigate prompt injection attacks."""
        if not text:
            return ""
        # Truncate to 3000 chars
        text = text[:3000]
        # Remove lines starting with suspicious patterns
        injection_prefixes = re.compile(
            r"^\s*(SYSTEM:|ASSISTANT:|\[INST\]|<\|im_start\|>|### Instruction)",
            re.MULTILINE | re.IGNORECASE,
        )
        text = injection_prefixes.sub("[contenu filtre]", text)
        # Replace known injection phrases
        injection_phrases = re.compile(
            r"(ignore previous|oublie les instructions|forget your instructions"
            r"|ignore all previous|ignore les instructions precedentes"
            r"|disregard previous|tu es maintenant)",
            re.IGNORECASE,
        )
        text = injection_phrases.sub("[contenu filtre]", text)
        return text

    @staticmethod
    def _extract_text(msg: email.message.Message) -> str:
        """Extract the plain-text body from a MIME message."""
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == "text/plain" and part.get("Content-Disposition") != "attachment":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        return payload.decode(charset, errors="replace")
            # Fallback: try text/html
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == "text/html" and part.get("Content-Disposition") != "attachment":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        return payload.decode(charset, errors="replace")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
        return ""

    def fetch_emails(
        self,
        date_filter: str = "month",
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Fetch emails from Gmail primary category with pagination.

        Uses X-GM-RAW to filter category:primary (Gmail IMAP extension).
        Returns ALL emails (read + unread) for the given period.

        Args:
            date_filter: 'today', 'week', or 'month' (default).
            page: Page number (1-based).
            page_size: Number of emails per page.

        Returns:
            Dict with 'emails', 'total', 'page', 'page_size', 'total_pages'.
        """
        imap = self._get_imap()
        try:
            imap.select("INBOX")

            # Build date SINCE clause
            if date_filter == "today":
                since = datetime.now().strftime("%d-%b-%Y")
            elif date_filter == "week":
                since = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
            else:  # month (default)
                since = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")

            # Use X-GM-RAW for Gmail category:primary filtering (no UNSEEN)
            search_criteria = f'(X-GM-RAW "category:primary" SINCE {since})'

            try:
                _, data = imap.search(None, search_criteria)
            except imaplib.IMAP4.error:
                # Fallback if X-GM-RAW not supported (non-Gmail server)
                logger.warning("X-GM-RAW not supported, falling back to basic SINCE")
                search_criteria = f'(SINCE {since})'
                _, data = imap.search(None, search_criteria)

            uids = data[0].split()
            total = len(uids)
            if not uids:
                return {"emails": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}

            # Most recent first
            uids = uids[::-1]

            # Paginate
            total_pages = (total + page_size - 1) // page_size
            page = max(1, min(page, total_pages))
            start = (page - 1) * page_size
            end = start + page_size
            page_uids = uids[start:end]

            results: list[dict[str, Any]] = []

            for uid in page_uids:
                _, msg_data = imap.fetch(uid, "(BODY.PEEK[])")
                if not msg_data or not msg_data[0]:
                    continue
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                body = self._extract_text(msg)
                preview = body[:300].strip() if body else ""

                date_str = msg.get("Date", "")
                try:
                    date_parsed = parsedate_to_datetime(date_str).isoformat()
                except Exception:
                    date_parsed = date_str

                attachments = self._extract_attachments(msg)
                results.append({
                    "uid": uid.decode(),
                    "from": self._decode_header_value(msg.get("From", "")),
                    "subject": self._decode_header_value(msg.get("Subject", "")),
                    "date": date_parsed,
                    "preview": preview,
                    "has_attachments": len(attachments) > 0,
                    "attachment_count": len(attachments),
                })
            return {
                "emails": results,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        finally:
            try:
                imap.logout()
            except Exception:
                pass

    def fetch_email(self, uid: str) -> dict[str, Any]:
        """Fetch a single email by UID (full body)."""
        imap = self._get_imap()
        try:
            imap.select("INBOX")
            _, msg_data = imap.fetch(uid.encode(), "(BODY.PEEK[])")
            if not msg_data or not msg_data[0]:
                return {"error": "Email introuvable"}

            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            body = self._extract_text(msg)

            date_str = msg.get("Date", "")
            try:
                date_parsed = parsedate_to_datetime(date_str).isoformat()
            except Exception:
                date_parsed = date_str

            attachments = self._extract_attachments(msg)
            return {
                "uid": uid,
                "from": self._decode_header_value(msg.get("From", "")),
                "to": self._decode_header_value(msg.get("To", "")),
                "subject": self._decode_header_value(msg.get("Subject", "")),
                "date": date_parsed,
                "body": body,
                "attachments": attachments,
            }
        finally:
            try:
                imap.logout()
            except Exception:
                pass

    def download_attachment(self, uid: str, part_index: int) -> dict[str, Any]:
        """Download a specific attachment from an email by UID and part index."""
        imap = self._get_imap()
        try:
            imap.select("INBOX")
            _, msg_data = imap.fetch(uid.encode(), "(BODY.PEEK[])")
            if not msg_data or not msg_data[0]:
                return {"error": "Email introuvable"}

            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            current_index = 0
            for part in msg.walk():
                if current_index == part_index:
                    payload = part.get_payload(decode=True)
                    if payload is None:
                        return {"error": "Piece jointe introuvable"}
                    filename = part.get_filename() or f"attachment_{part_index}"
                    if isinstance(filename, bytes):
                        filename = filename.decode("utf-8", errors="replace")
                    else:
                        filename = self._decode_header_value(filename)
                    return {
                        "data": payload,
                        "filename": filename,
                        "content_type": part.get_content_type(),
                    }
                current_index += 1

            return {"error": "Index de piece jointe invalide"}
        finally:
            try:
                imap.logout()
            except Exception:
                pass

    # -- LLM helpers ------------------------------------------------------------

    def _get_openai(self) -> OpenAI:
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def summarize_unread(self, max_results: int = 20, uids: list[str] | None = None) -> dict[str, Any]:
        """Summarize recent emails using LLM.

        Args:
            max_results: Max emails to summarize when no UIDs given.
            uids: If provided, summarize only these specific emails (full body).
        """
        if uids:
            # Validate UIDs: must be numeric strings, max 30
            valid_uids = [u for u in uids[:30] if u.isdigit()]
            if not valid_uids:
                return {"summary": "Aucun UID valide.", "count": 0}

            # Fetch each selected email individually with full body
            emails_data = []
            for uid in valid_uids:
                em = self.fetch_email(uid)
                if "error" not in em:
                    emails_data.append(em)
            if not emails_data:
                return {"summary": "Aucun mail trouve.", "count": 0}

            lines = []
            for e in emails_data:
                safe_body = self._sanitize_for_llm(e.get("body", ""))
                safe_from = self._sanitize_for_llm(e.get("from", ""))[:150]
                safe_subject = self._sanitize_for_llm(e.get("subject", ""))[:200]
                lines.append(
                    f"- De: {safe_from} | Sujet: {safe_subject} | {e['date']}\n  {safe_body}"
                )
            email_text = "\n".join(lines)
            count = len(emails_data)
        else:
            result = self.fetch_emails(date_filter="month", page=1, page_size=max_results)
            emails = result["emails"]
            if not emails:
                return {"summary": "Aucun mail non lu.", "count": 0}

            lines = []
            for e in emails:
                safe_preview = self._sanitize_for_llm(e['preview'])
                safe_from = self._sanitize_for_llm(e.get('from', ''))[:150]
                safe_subject = self._sanitize_for_llm(e.get('subject', ''))[:200]
                lines.append(f"- De: {safe_from} | Sujet: {safe_subject} | {e['date']}\n  {safe_preview}")
            email_text = "\n".join(lines)
            count = len(emails)

        client = self._get_openai()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un assistant qui resume des emails. "
                        "Fais un resume clair et structure en francais. "
                        "Indique les actions requises s'il y en a."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Resume ces {count} mails :\n\n{email_text}",
                },
            ],
            temperature=0.3,
        )
        return {
            "summary": resp.choices[0].message.content,
            "count": count,
        }

    def draft_reply(self, uid: str, instructions: str) -> dict[str, Any]:
        """Generate a draft reply for a given email using LLM."""
        original = self.fetch_email(uid)
        if "error" in original:
            return original

        client = self._get_openai()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un assistant de redaction d'emails. "
                        "Redige une reponse professionnelle en francais "
                        "en suivant les instructions donnees."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Email original :\n"
                        f"De: {original['from']}\n"
                        f"Sujet: {original['subject']}\n"
                        f"Corps:\n{self._sanitize_for_llm(original['body'])}\n\n"
                        f"Instructions pour la reponse : {instructions}"
                    ),
                },
            ],
            temperature=0.4,
        )
        return {
            "draft": resp.choices[0].message.content,
            "original_subject": original["subject"],
            "to": original["from"],
        }

    def improve_text(self, text: str) -> dict[str, Any]:
        """Improve/complete a text using LLM (no original email context)."""
        client = self._get_openai()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un assistant de redaction d'emails. "
                        "Ameliore, complete ou redige le texte fourni "
                        "pour en faire un email professionnel en francais. "
                        "Retourne uniquement le texte ameliore."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Texte a ameliorer :\n{text}",
                },
            ],
            temperature=0.4,
        )
        return {"draft": resp.choices[0].message.content}

    # -- categories -------------------------------------------------------------

    def _load_categories(self) -> dict[str, Any]:
        """Load categories from JSON file."""
        if CATEGORIES_FILE.exists():
            return json.loads(CATEGORIES_FILE.read_text(encoding="utf-8"))
        return {"categories": {}, "rules": [], "statuses": {}, "emails": {}}

    def _save_categories(self, data: dict[str, Any]) -> None:
        """Save categories to JSON file."""
        CATEGORIES_FILE.parent.mkdir(parents=True, exist_ok=True)
        CATEGORIES_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def get_categories(self) -> dict[str, Any]:
        """Return categories definitions and email-category mapping."""
        return self._load_categories()

    def set_email_category(self, uid: str, category: str) -> dict[str, Any]:
        """Assign a category to an email (manual override)."""
        data = self._load_categories()
        if category not in data.get("categories", {}):
            return {"error": f"Categorie inconnue: {category}"}
        emails = data.setdefault("emails", {})
        if uid in emails:
            emails[uid]["category"] = category
            emails[uid]["manual"] = True
        else:
            emails[uid] = {"category": category, "status": "Nouveau", "manual": True}
        self._save_categories(data)
        return {"success": True, "uid": uid, "category": category}

    def remove_email_category(self, uid: str) -> dict[str, Any]:
        """Remove category from an email."""
        data = self._load_categories()
        data.get("emails", {}).pop(uid, None)
        self._save_categories(data)
        return {"success": True, "uid": uid}

    # -- auto-classification ----------------------------------------------------

    def classify_email(self, sender: str, subject: str) -> str:
        """Classify an email based on rules (sender/subject matching).

        First match wins. Default = 'Personnel'.
        """
        data = self._load_categories()
        rules = data.get("rules", [])
        sender_lower = sender.lower()
        subject_lower = subject.lower()

        for rule in rules:
            # Match sender keywords
            for kw in rule.get("senders", []):
                if kw in sender_lower:
                    return rule["category"]
            # Match subject keywords
            for kw in rule.get("subjects", []):
                if kw and kw in subject_lower:
                    return rule["category"]

        return "Personnel"

    def auto_classify_emails(self, emails_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Auto-classify emails and enrich them with category + status.

        Phase 1: Classify via keyword rules.
        Phase 2: Batch-classify remaining 'Personnel' emails via LLM.
        Returns the enriched email list.
        """
        data = self._load_categories()
        stored = data.setdefault("emails", {})
        changed = False

        # Phase 1: Rule-based classification
        for em in emails_list:
            uid = em.get("uid", "")
            if not uid:
                continue

            sender = em.get("from", "")
            subject = em.get("subject", "")

            if uid not in stored:
                category = self.classify_email(sender, subject)
                stored[uid] = {
                    "category": category,
                    "status": "Nouveau",
                    "from": sender,
                    "subject": subject,
                    "preview": em.get("preview", ""),
                }
                changed = True
            elif not stored[uid].get("manual") and not stored[uid].get("ai"):
                new_cat = self.classify_email(sender, subject)
                if new_cat != "Personnel" and stored[uid].get("category") != new_cat:
                    stored[uid]["category"] = new_cat
                    changed = True
                # Update metadata for LLM fallback
                stored[uid]["from"] = sender
                stored[uid]["subject"] = subject
                stored[uid]["preview"] = em.get("preview", "")

        # Phase 2: LLM fallback for emails still in "Personnel"
        to_llm = []
        for em in emails_list:
            uid = em.get("uid", "")
            if uid and uid in stored:
                info = stored[uid]
                if info.get("category") == "Personnel" and not info.get("manual") and not info.get("ai"):
                    to_llm.append({
                        "uid": uid,
                        "from": em.get("from", ""),
                        "subject": em.get("subject", ""),
                        "preview": em.get("preview", ""),
                    })

        if to_llm:
            try:
                llm_results = self.classify_emails_batch_llm(to_llm)
                for uid, cat in llm_results.items():
                    if uid in stored:
                        stored[uid]["category"] = cat
                        stored[uid]["ai"] = True
                        changed = True
            except Exception as exc:
                logger.warning("LLM classification fallback failed: %s", exc)

        if changed:
            self._save_categories(data)

        # Build enriched list
        enriched = []
        for em in emails_list:
            uid = em.get("uid", "")
            if not uid:
                enriched.append(em)
                continue
            info = stored.get(uid, {})
            enriched.append({
                **em,
                "category": info.get("category", "Personnel"),
                "status": info.get("status", "Nouveau"),
                "ai": info.get("ai", False),
            })

        return enriched

    # -- LLM classification -----------------------------------------------------

    _MAX_LLM_BATCH = 30  # Max emails per LLM classification call

    def classify_emails_batch_llm(self, emails_to_classify: list[dict[str, Any]]) -> dict[str, str]:
        """Classify a batch of emails using LLM.

        Args:
            emails_to_classify: List of {uid, from, subject, preview}.

        Returns:
            Dict mapping uid -> category name.
        """
        if not emails_to_classify:
            return {}

        # Limit batch size to prevent oversized prompts
        emails_to_classify = emails_to_classify[: self._MAX_LLM_BATCH]

        data = self._load_categories()
        cat_names = list(data.get("categories", {}).keys())

        items = []
        for em in emails_to_classify:
            # Sanitize all user-controlled fields before injecting into prompt
            safe_from = self._sanitize_for_llm(em.get("from", ""))[:150]
            safe_subject = self._sanitize_for_llm(em.get("subject", ""))[:200]
            safe_preview = self._sanitize_for_llm(em.get("preview", ""))[:200]
            items.append(
                f"- uid={em['uid']} | from={safe_from} | subject={safe_subject} | preview={safe_preview}"
            )
        email_text = "\n".join(items)

        client = self._get_openai()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un classificateur d'emails. "
                        "Classe chaque email dans UNE SEULE des categories suivantes : "
                        f"{', '.join(cat_names)}. "
                        "Reponds UNIQUEMENT en JSON valide : {\"uid\": \"categorie\", ...}. "
                        "Pas d'explication, pas de markdown, juste le JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Classe ces emails :\n\n{email_text}",
                },
            ],
            temperature=0.1,
        )

        raw = resp.choices[0].message.content.strip()
        # Extract JSON from potential markdown code block
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("LLM classification JSON parse failed: %s", raw[:500])
            return {}

        # Validate categories
        valid = {}
        for uid, cat in result.items():
            if cat in cat_names:
                valid[str(uid)] = cat
            else:
                valid[str(uid)] = "Personnel"
        return valid

    def classify_ai_fallback(self) -> dict[str, Any]:
        """Reclassify emails stuck in 'Personnel' using LLM.

        Only processes emails not already classified by AI or manually.
        Returns count of reclassified emails.
        """
        data = self._load_categories()
        stored = data.get("emails", {})

        to_classify = []
        for uid, info in stored.items():
            if info.get("category") == "Personnel" and not info.get("manual") and not info.get("ai"):
                to_classify.append({
                    "uid": uid,
                    "from": info.get("from", ""),
                    "subject": info.get("subject", ""),
                    "preview": info.get("preview", ""),
                })

        if not to_classify:
            return {"reclassified": 0, "message": "Aucun mail a reclassifier."}

        classifications = self.classify_emails_batch_llm(to_classify)

        changed = 0
        for uid, cat in classifications.items():
            if uid in stored and cat != "Personnel":
                stored[uid]["category"] = cat
                stored[uid]["ai"] = True
                changed += 1
            elif uid in stored:
                # Mark as AI-processed even if still Personnel
                stored[uid]["ai"] = True

        if changed:
            self._save_categories(data)

        return {"reclassified": changed, "message": f"{changed} mail(s) reclassifie(s) par IA."}

    # -- status management ------------------------------------------------------

    def set_email_status(self, uid: str, status: str) -> dict[str, Any]:
        """Set email status (Nouveau / En cours / Traite)."""
        if status not in VALID_STATUSES:
            return {"error": f"Statut invalide: {status}. Valides: {', '.join(VALID_STATUSES)}"}

        data = self._load_categories()
        emails = data.setdefault("emails", {})
        if uid in emails:
            emails[uid]["status"] = status
        else:
            emails[uid] = {"category": "Personnel", "status": status}
        self._save_categories(data)
        return {"success": True, "uid": uid, "status": status}

    # -- sending ----------------------------------------------------------------

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: list[tuple[str, str, bytes]] | None = None,
    ) -> dict[str, Any]:
        """Send an email via SMTP SSL.

        Args:
            to: Recipient address.
            subject: Email subject.
            body: Plain-text body.
            attachments: Optional list of (filename, content_type, data) tuples.
        """
        if attachments:
            msg = MIMEMultipart("mixed")
            msg["From"] = self.address
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))
            for filename, content_type, data in attachments:
                maintype, subtype = content_type.split("/", 1) if "/" in content_type else ("application", "octet-stream")
                part = MIMEBase(maintype, subtype)
                part.set_payload(data)
                email.encoders.encode_base64(part)
                part.add_header("Content-Disposition", "attachment", filename=filename)
                msg.attach(part)
        else:
            msg = MIMEText(body, "plain", "utf-8")
            msg["From"] = self.address
            msg["To"] = to
            msg["Subject"] = subject

        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
                smtp.login(self.address, self.app_password)
                smtp.send_message(msg)
            logger.info("Email sent to %s: %s", to, subject)
            return {"success": True, "message": f"Email envoye a {to}"}
        except Exception as exc:
            logger.error("Failed to send email: %s", exc)
            return {"success": False, "error": str(exc)}


# Module-level singleton
gmail_service = GmailService()
