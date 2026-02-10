"""
MCP (Model Context Protocol) -- Package principal.

Centralise l'enregistrement, la decouverte et la gestion des serveurs MCP.
Chaque sous-package correspond a une categorie de la checklist MCP.
"""

from mcp.registry import MCPRegistry, mcp_registry  # noqa: F401
from mcp.base import BaseMCPServer, MCPStatus  # noqa: F401

__all__ = ["MCPRegistry", "mcp_registry", "BaseMCPServer", "MCPStatus"]
