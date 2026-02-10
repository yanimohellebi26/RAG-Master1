"""
MCP Server -- Filesystem.

Indexer des fichiers locaux hors du dossier Master1/.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class FilesystemServer(BaseMCPServer):
    SERVER_ID = "filesystem"
    SERVER_NAME = "Filesystem"
    CATEGORY = "content"
    DESCRIPTION = "Indexer des fichiers locaux hors du dossier Master1/"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="scan_directory",
                description="Scanner un dossier et lister les fichiers",
                parameters={"path": "str", "extensions": "list[str]"},
                required_params=["path"],
            ),
            MCPToolDefinition(
                name="index_files",
                description="Indexer les fichiers d'un dossier dans ChromaDB",
                parameters={"path": "str", "subject": "str"},
                required_params=["path"],
            ),
            MCPToolDefinition(
                name="read_file",
                description="Lire le contenu d'un fichier",
                parameters={"path": "str"},
                required_params=["path"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Filesystem -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
