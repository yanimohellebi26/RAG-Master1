"""
MCP Server -- Gmail / Email.

Gestion des mails : lire, envoyer, trier, resumer, repondre.
Utilise le GmailService (IMAP/SMTP + App Password) en interne.
"""

from __future__ import annotations

from typing import Any

from mcp.base import BaseMCPServer, MCPToolDefinition


class GmailServer(BaseMCPServer):
    SERVER_ID = "gmail"
    SERVER_NAME = "Gmail"
    CATEGORY = "personal"
    DESCRIPTION = "Gestion complete des mails (lire, envoyer, trier, resumer)"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="read_emails",
                description="Lire les mails non lus ou filtres",
                parameters={"query": "str", "max_results": "int"},
            ),
            MCPToolDefinition(
                name="send_email",
                description="Envoyer un email",
                parameters={"to": "str", "subject": "str", "body": "str"},
                required_params=["to", "subject", "body"],
            ),
            MCPToolDefinition(
                name="summarize_emails",
                description="Resumer les mails non lus",
                parameters={"max_results": "int"},
            ),
        ]

    async def connect(self) -> bool:
        """Connect via GmailService (IMAP App Password)."""
        try:
            from api.services.gmail import gmail_service
            if not gmail_service.available:
                self.logger.warning("Gmail credentials missing in .env")
                return False
            success = gmail_service.connect()
            if success:
                self._connected = True
            return success
        except Exception as exc:
            self.logger.error("Gmail MCP connect failed: %s", exc)
            return False

    async def disconnect(self) -> None:
        self._connected = False

    async def health(self) -> bool:
        """Check connection by delegating to the service."""
        if not self.is_connected:
            return False
        try:
            from api.services.gmail import gmail_service
            return gmail_service.connected
        except Exception:
            return False
