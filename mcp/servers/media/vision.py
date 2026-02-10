"""
MCP Server -- Vision (GPT-4 Vision).

Lire et decrire schemas, diagrammes, graphes.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class VisionServer(BaseMCPServer):
    SERVER_ID = "vision"
    SERVER_NAME = "Vision (GPT-4V)"
    CATEGORY = "media"
    DESCRIPTION = "Lire et decrire schemas, diagrammes, graphes"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="describe_image",
                description="Decrire le contenu d'une image",
                parameters={"image_path": "str", "prompt": "str"},
                required_params=["image_path"],
            ),
            MCPToolDefinition(
                name="extract_diagram",
                description="Extraire la structure d'un diagramme/schema",
                parameters={"image_path": "str"},
                required_params=["image_path"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Vision -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
