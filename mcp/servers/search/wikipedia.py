"""
MCP Server -- Wikipedia.

Definitions et concepts fondamentaux.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class WikipediaServer(BaseMCPServer):
    SERVER_ID = "wikipedia"
    SERVER_NAME = "Wikipedia"
    CATEGORY = "search"
    DESCRIPTION = "Definitions rapides et concepts fondamentaux"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="search",
                description="Rechercher sur Wikipedia",
                parameters={"query": "str", "lang": "str"},
                required_params=["query"],
            ),
            MCPToolDefinition(
                name="get_summary",
                description="Obtenir le resume d'un article Wikipedia",
                parameters={"title": "str", "lang": "str"},
                required_params=["title"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Wikipedia -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
