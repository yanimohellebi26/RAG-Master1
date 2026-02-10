"""
MCP Server -- Code Interpreter.

Executer du code Python/Java directement, sandbox securisee.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class CodeInterpreterServer(BaseMCPServer):
    SERVER_ID = "code-interpreter"
    SERVER_NAME = "Code Interpreter"
    CATEGORY = "code"
    DESCRIPTION = "Executer du code Python/Java directement"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="execute_code",
                description="Executer du code dans un sandbox",
                parameters={"code": "str", "language": "str", "timeout": "int"},
                required_params=["code"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Code Interpreter -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
