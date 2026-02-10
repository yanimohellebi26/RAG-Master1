"""
MCP Server -- Google Drive.

Acces aux documents partages (slides, annales, PDF).
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class GoogleDriveServer(BaseMCPServer):
    SERVER_ID = "google-drive"
    SERVER_NAME = "Google Drive"
    CATEGORY = "content"
    DESCRIPTION = "Acces aux documents partages (slides, annales, PDF)"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="list_files",
                description="Lister les fichiers d'un dossier Drive",
                parameters={"folder_id": "str", "query": "str"},
            ),
            MCPToolDefinition(
                name="download_file",
                description="Telecharger un fichier depuis Drive",
                parameters={"file_id": "str", "output_path": "str"},
                required_params=["file_id"],
            ),
            MCPToolDefinition(
                name="sync_folder",
                description="Synchroniser un dossier Drive vers ChromaDB",
                parameters={"folder_id": "str", "subject": "str"},
                required_params=["folder_id"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Google Drive -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
