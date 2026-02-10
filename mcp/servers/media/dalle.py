"""
MCP Server -- DALL-E / Image Generation.

Generer des schemas explicatifs et diagrammes.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class DalleServer(BaseMCPServer):
    SERVER_ID = "dalle"
    SERVER_NAME = "DALL-E"
    CATEGORY = "media"
    DESCRIPTION = "Generer des schemas explicatifs et diagrammes"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="generate_image",
                description="Generer une image a partir d'un prompt",
                parameters={"prompt": "str", "size": "str", "style": "str"},
                required_params=["prompt"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("DALL-E -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
