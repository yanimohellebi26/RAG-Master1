"""
MCP Server -- Docker.

Execution dans un environnement isole (conteneurs).
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class DockerServer(BaseMCPServer):
    SERVER_ID = "docker"
    SERVER_NAME = "Docker"
    CATEGORY = "code"
    DESCRIPTION = "Execution dans des conteneurs Docker isoles"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="run_container",
                description="Lancer un conteneur Docker",
                parameters={"image": "str", "command": "str", "env": "dict"},
                required_params=["image"],
            ),
            MCPToolDefinition(
                name="list_containers",
                description="Lister les conteneurs en cours",
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Docker -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
