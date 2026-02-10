"""
MCP Server -- ArXiv.

Articles de recherche (IA, algo, systemes distribues).
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class ArxivServer(BaseMCPServer):
    SERVER_ID = "arxiv"
    SERVER_NAME = "ArXiv"
    CATEGORY = "search"
    DESCRIPTION = "Articles de recherche academiques"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="search_papers",
                description="Rechercher des articles sur ArXiv",
                parameters={"query": "str", "max_results": "int"},
                required_params=["query"],
            ),
            MCPToolDefinition(
                name="get_paper",
                description="Recuperer les details d'un article ArXiv",
                parameters={"arxiv_id": "str"},
                required_params=["arxiv_id"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("ArXiv -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
