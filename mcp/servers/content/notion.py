"""
MCP Server -- Notion.

Connecter les notes personnelles Notion comme source de connaissances.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class NotionServer(BaseMCPServer):
    SERVER_ID = "notion"
    SERVER_NAME = "Notion"
    CATEGORY = "content"
    DESCRIPTION = "Connecter les notes personnelles Notion comme source"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="search_pages",
                description="Rechercher dans les pages Notion",
                parameters={"query": "str"},
                required_params=["query"],
            ),
            MCPToolDefinition(
                name="get_page",
                description="Recuperer le contenu d'une page Notion",
                parameters={"page_id": "str"},
                required_params=["page_id"],
            ),
            MCPToolDefinition(
                name="sync_pages",
                description="Synchroniser les pages Notion vers ChromaDB",
                parameters={"database_id": "str"},
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Notion -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
