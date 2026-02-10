"""
MCP Server -- Todoist.

Taches, checklists par matiere, suivi de progression.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class TodoistServer(BaseMCPServer):
    SERVER_ID = "todoist"
    SERVER_NAME = "Todoist"
    CATEGORY = "organization"
    DESCRIPTION = "Taches, checklists par matiere et suivi de progression"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="list_tasks",
                description="Lister les taches en cours",
                parameters={"project": "str", "filter": "str"},
            ),
            MCPToolDefinition(
                name="create_task",
                description="Creer une nouvelle tache",
                parameters={"title": "str", "project": "str", "due": "str"},
                required_params=["title"],
            ),
            MCPToolDefinition(
                name="complete_task",
                description="Marquer une tache comme terminee",
                parameters={"task_id": "str"},
                required_params=["task_id"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Todoist -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
