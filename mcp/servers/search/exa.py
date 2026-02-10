"""
MCP Server -- Exa.

Recherche semantique sur le web (articles par sens).
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class ExaServer(BaseMCPServer):
    SERVER_ID = "exa"
    SERVER_NAME = "Exa"
    CATEGORY = "search"
    DESCRIPTION = "Recherche semantique sur le web (articles par sens)"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="semantic_search",
                description="Recherche semantique web via Exa",
                parameters={"query": "str", "num_results": "int"},
                required_params=["query"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Exa -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
