"""
MCP Server -- Gmail / Email.

Gestion des mails : lire, envoyer, trier, resumer, repondre.
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
        # TODO: OAuth2 authentication with Gmail API
        self.logger.info("Gmail connection -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
