"""
MCP Server -- Brave Search / Tavily.

Enrichissement web : recherche et sources citees dans les reponses.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class BraveSearchServer(BaseMCPServer):
    SERVER_ID = "brave-search"
    SERVER_NAME = "Brave Search"
    CATEGORY = "search"
    DESCRIPTION = "Recherche web pour completer les reponses RAG"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="web_search",
                description="Recherche web via Brave Search",
                parameters={"query": "str", "max_results": "int"},
                required_params=["query"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Brave Search -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
