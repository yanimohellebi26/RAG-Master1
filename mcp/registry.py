"""
MCP Registry -- Enregistrement et gestion centralisee des serveurs MCP.

Usage:
    from mcp import mcp_registry

    mcp_registry.register(GmailServer)
    mcp_registry.configure_all(config)

    servers = mcp_registry.list_servers()
    gmail = mcp_registry.get("gmail")
"""

from __future__ import annotations

import logging
from typing import Any, Type

from mcp.base import BaseMCPServer, MCPStatus

logger = logging.getLogger(__name__)


class MCPRegistry:
    """Registre central de tous les serveurs MCP disponibles."""

    def __init__(self) -> None:
        self._server_classes: dict[str, Type[BaseMCPServer]] = {}
        self._instances: dict[str, BaseMCPServer] = {}
        self._global_config: dict[str, Any] = {}

    # -- Enregistrement -----------------------------------------------------

    def register(self, server_class: Type[BaseMCPServer]) -> None:
        """Enregistrer une classe de serveur MCP."""
        server_id = server_class.SERVER_ID
        if not server_id:
            raise ValueError(f"SERVER_ID manquant pour {server_class.__name__}")
        if server_id in self._server_classes:
            logger.warning(f"MCP server '{server_id}' already registered, overwriting.")
        self._server_classes[server_id] = server_class
        logger.debug(f"Registered MCP server: {server_id}")

    # -- Configuration ------------------------------------------------------

    def configure_all(self, mcp_config: dict[str, Any]) -> None:
        """
        Configurer tous les serveurs a partir de la section 'mcp' du config.yaml.

        Attendu: mcp_config = {"gmail": {"enabled": true, ...}, ...}
        """
        self._global_config = mcp_config
        for server_id, server_class in self._server_classes.items():
            server_cfg = mcp_config.get(server_id, {})
            self._instances[server_id] = server_class(config=server_cfg)
            status = "enabled" if server_cfg.get("enabled") else "disabled"
            logger.info(f"MCP {server_id}: {status}")

    # -- Acces aux serveurs -------------------------------------------------

    def get(self, server_id: str) -> BaseMCPServer | None:
        """Recuperer l'instance d'un serveur par son ID."""
        return self._instances.get(server_id)

    def list_servers(self) -> list[dict[str, Any]]:
        """Liste de tous les serveurs avec leur statut."""
        result = []
        for server_id, server_class in self._server_classes.items():
            instance = self._instances.get(server_id)
            if instance:
                result.append(instance.info.to_dict())
            else:
                result.append({
                    "id": server_id,
                    "name": server_class.SERVER_NAME,
                    "category": server_class.CATEGORY,
                    "description": server_class.DESCRIPTION,
                    "status": MCPStatus.DISABLED.value,
                    "tools": [],
                })
        return result

    def list_by_category(self, category: str) -> list[dict[str, Any]]:
        """Filtrer les serveurs par categorie."""
        return [s for s in self.list_servers() if s["category"] == category]

    def get_enabled(self) -> list[BaseMCPServer]:
        """Retourner uniquement les serveurs actives."""
        return [s for s in self._instances.values() if s.is_enabled]

    def get_connected(self) -> list[BaseMCPServer]:
        """Retourner uniquement les serveurs connectes."""
        return [s for s in self._instances.values() if s.is_connected]

    # -- Lifecycle ----------------------------------------------------------

    async def connect_enabled(self) -> dict[str, bool]:
        """Connecter tous les serveurs actives. Retourne {id: success}."""
        results = {}
        for server in self.get_enabled():
            success = await server.ensure_connected()
            results[server.SERVER_ID] = success
        return results

    async def disconnect_all(self) -> None:
        """Deconnecter proprement tous les serveurs."""
        for server in self._instances.values():
            if server.is_connected:
                await server.safe_disconnect()

    # -- Stats --------------------------------------------------------------

    @property
    def stats(self) -> dict[str, int]:
        """Statistiques du registre."""
        servers = list(self._instances.values())
        return {
            "total": len(self._server_classes),
            "configured": len(servers),
            "enabled": sum(1 for s in servers if s.is_enabled),
            "connected": sum(1 for s in servers if s.is_connected),
        }


# -- Singleton global -------------------------------------------------------

mcp_registry = MCPRegistry()
