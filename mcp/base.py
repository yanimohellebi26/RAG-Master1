"""
Base MCP Server -- Classe abstraite pour tous les serveurs MCP.

Chaque serveur MCP herite de BaseMCPServer et implemente :
  - connect()    : etablir la connexion au service
  - disconnect() : fermer la connexion proprement
  - health()     : verifier que le service est accessible
  - tools()      : liste des outils exposes par ce serveur
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MCPStatus(str, Enum):
    """Etat d'un serveur MCP."""
    DISABLED = "disabled"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPToolDefinition:
    """Definition d'un outil expose par un serveur MCP."""
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    required_params: list[str] = field(default_factory=list)


@dataclass
class MCPServerInfo:
    """Metadonnees d'un serveur MCP."""
    id: str
    name: str
    category: str
    description: str
    status: MCPStatus = MCPStatus.DISABLED
    version: str = "0.1.0"
    tools: list[MCPToolDefinition] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "status": self.status.value,
            "version": self.version,
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                    "required_params": t.required_params,
                }
                for t in self.tools
            ],
        }


class BaseMCPServer(ABC):
    """
    Classe abstraite pour un serveur MCP.

    Chaque implementation concrete doit definir :
      - SERVER_ID   : identifiant unique (ex: "gmail", "brave-search")
      - SERVER_NAME : nom affichable (ex: "Gmail", "Brave Search")
      - CATEGORY    : categorie de la checklist
      - DESCRIPTION : description courte

    Et implementer les methodes abstraites.
    """

    SERVER_ID: str = ""
    SERVER_NAME: str = ""
    CATEGORY: str = ""
    DESCRIPTION: str = ""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self._status = MCPStatus.DISABLED
        self._tools: list[MCPToolDefinition] = []
        self.logger = logging.getLogger(f"mcp.{self.SERVER_ID}")

    # -- Proprietes ---------------------------------------------------------

    @property
    def status(self) -> MCPStatus:
        return self._status

    @property
    def info(self) -> MCPServerInfo:
        return MCPServerInfo(
            id=self.SERVER_ID,
            name=self.SERVER_NAME,
            category=self.CATEGORY,
            description=self.DESCRIPTION,
            status=self._status,
            tools=self._tools,
        )

    @property
    def is_connected(self) -> bool:
        return self._status == MCPStatus.CONNECTED

    @property
    def is_enabled(self) -> bool:
        return self.config.get("enabled", False)

    # -- Methodes abstraites ------------------------------------------------

    @abstractmethod
    async def connect(self) -> bool:
        """Etablir la connexion au service externe. Retourne True si OK."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Fermer la connexion proprement."""
        ...

    @abstractmethod
    async def health(self) -> bool:
        """Verifier que le service est accessible."""
        ...

    @abstractmethod
    def tools(self) -> list[MCPToolDefinition]:
        """Retourner la liste des outils exposes par ce serveur."""
        ...

    # -- Methodes utilitaires -----------------------------------------------

    async def ensure_connected(self) -> bool:
        """Se connecter si pas deja connecte."""
        if self.is_connected:
            return True
        if not self.is_enabled:
            self.logger.debug(f"MCP {self.SERVER_ID} is disabled.")
            return False
        self._status = MCPStatus.CONNECTING
        try:
            success = await self.connect()
            self._status = MCPStatus.CONNECTED if success else MCPStatus.ERROR
            return success
        except Exception as exc:
            self.logger.error(f"Connection failed for {self.SERVER_ID}: {exc}")
            self._status = MCPStatus.ERROR
            return False

    async def safe_disconnect(self) -> None:
        """Deconnecter en gerant les erreurs."""
        try:
            await self.disconnect()
        except Exception as exc:
            self.logger.warning(f"Error disconnecting {self.SERVER_ID}: {exc}")
        finally:
            self._status = MCPStatus.DISCONNECTED

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """
        Executer un outil du serveur par son nom.
        A surcharger dans les implementations concretes.
        """
        raise NotImplementedError(
            f"Tool '{tool_name}' not implemented in {self.SERVER_ID}"
        )
