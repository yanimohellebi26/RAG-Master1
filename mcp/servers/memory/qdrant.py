"""
MCP Server -- Qdrant.

Alternative/complement vectoriel a ChromaDB.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class QdrantServer(BaseMCPServer):
    SERVER_ID = "qdrant"
    SERVER_NAME = "Qdrant"
    CATEGORY = "memory"
    DESCRIPTION = "Base vectorielle alternative/complement a ChromaDB"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="search",
                description="Recherche vectorielle dans Qdrant",
                parameters={"query": "str", "collection": "str", "limit": "int"},
                required_params=["query"],
            ),
            MCPToolDefinition(
                name="upsert",
                description="Inserer/mettre a jour des vecteurs",
                parameters={"collection": "str", "documents": "list"},
                required_params=["collection", "documents"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Qdrant -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
