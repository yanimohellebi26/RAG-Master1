"""
MCP Server -- Discord.

Partage collaboratif avec le groupe d'etude.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class DiscordServer(BaseMCPServer):
    SERVER_ID = "discord"
    SERVER_NAME = "Discord"
    CATEGORY = "communication"
    DESCRIPTION = "Partage collaboratif avec le groupe d'etude"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="send_message",
                description="Envoyer un message dans un canal Discord",
                parameters={"channel_id": "str", "content": "str"},
                required_params=["channel_id", "content"],
            ),
            MCPToolDefinition(
                name="read_messages",
                description="Lire les derniers messages d'un canal",
                parameters={"channel_id": "str", "limit": "int"},
                required_params=["channel_id"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Discord -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
