"""
MCP Server -- Terminal.

Controle du terminal local : executer des commandes, gerer l'environnement.
"""

from __future__ import annotations

from typing import Any

from mcp.base import BaseMCPServer, MCPToolDefinition


class TerminalServer(BaseMCPServer):
    SERVER_ID = "terminal"
    SERVER_NAME = "Terminal"
    CATEGORY = "personal"
    DESCRIPTION = "Execution de commandes shell et gestion de l'environnement"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="execute_command",
                description="Executer une commande shell",
                parameters={"command": "str", "cwd": "str", "timeout": "int"},
                required_params=["command"],
            ),
            MCPToolDefinition(
                name="list_processes",
                description="Lister les processus en cours",
            ),
        ]

    async def connect(self) -> bool:
        # TODO: Setup sandboxed shell execution
        self.logger.info("Terminal connection -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
