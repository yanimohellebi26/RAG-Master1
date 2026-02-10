"""
MCP Server -- Jupyter.

Notebooks interactifs pour les TPs.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class JupyterServer(BaseMCPServer):
    SERVER_ID = "jupyter"
    SERVER_NAME = "Jupyter"
    CATEGORY = "code"
    DESCRIPTION = "Notebooks interactifs pour les TPs"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="create_notebook",
                description="Creer un notebook Jupyter",
                parameters={"title": "str", "cells": "list"},
                required_params=["title"],
            ),
            MCPToolDefinition(
                name="run_cell",
                description="Executer une cellule de notebook",
                parameters={"notebook_path": "str", "cell_index": "int"},
                required_params=["notebook_path", "cell_index"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Jupyter -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
