"""
MCP Server -- SQLite.

Historique, scores, progression et analytics.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class SQLiteServer(BaseMCPServer):
    SERVER_ID = "sqlite"
    SERVER_NAME = "SQLite"
    CATEGORY = "memory"
    DESCRIPTION = "Historique, scores, progression et analytics"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="query",
                description="Executer une requete SQL",
                parameters={"sql": "str", "params": "list"},
                required_params=["sql"],
            ),
            MCPToolDefinition(
                name="get_stats",
                description="Obtenir les statistiques de progression",
                parameters={"subject": "str"},
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("SQLite -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
