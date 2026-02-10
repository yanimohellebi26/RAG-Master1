"""
MCP Server -- Memory.

Preferences et personnalisation persistantes entre les sessions.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class MemoryServer(BaseMCPServer):
    SERVER_ID = "memory"
    SERVER_NAME = "Memory"
    CATEGORY = "memory"
    DESCRIPTION = "Preferences et personnalisation persistantes"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="store",
                description="Stocker une information en memoire",
                parameters={"key": "str", "value": "str", "namespace": "str"},
                required_params=["key", "value"],
            ),
            MCPToolDefinition(
                name="recall",
                description="Recuperer une information depuis la memoire",
                parameters={"key": "str", "namespace": "str"},
                required_params=["key"],
            ),
            MCPToolDefinition(
                name="search_memory",
                description="Recherche semantique dans la memoire",
                parameters={"query": "str", "limit": "int"},
                required_params=["query"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Memory -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
