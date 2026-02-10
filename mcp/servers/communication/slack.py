"""
MCP Server -- Slack.

Communication d'equipe et notifications.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class SlackServer(BaseMCPServer):
    SERVER_ID = "slack"
    SERVER_NAME = "Slack"
    CATEGORY = "communication"
    DESCRIPTION = "Communication d'equipe et notifications"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="send_message",
                description="Envoyer un message dans un canal Slack",
                parameters={"channel": "str", "text": "str"},
                required_params=["channel", "text"],
            ),
            MCPToolDefinition(
                name="read_messages",
                description="Lire les derniers messages d'un canal",
                parameters={"channel": "str", "limit": "int"},
                required_params=["channel"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Slack -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
