"""
Google Drive Service -- Interface haut-niveau pour le MCP Google Drive.

Utilise par le blueprint /api/gdrive pour exposer les fonctionnalites
sans coupler directement Flask au MCP server.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.servers.content.google_drive import (
    GoogleDriveServer,
    GDRIVE_AVAILABLE,
)

logger = logging.getLogger(__name__)


class GoogleDriveService:
    """Service singleton for Google Drive operations."""

    def __init__(self) -> None:
        self._server: GoogleDriveServer | None = None

    @property
    def available(self) -> bool:
        return GDRIVE_AVAILABLE

    @property
    def server(self) -> GoogleDriveServer:
        if self._server is None:
            from core.config import CONFIG
            mcp_cfg = CONFIG.get("mcp", {}).get("google-drive", {})
            self._server = GoogleDriveServer(config=mcp_cfg)
        return self._server

    @property
    def connected(self) -> bool:
        return self._server is not None and self._server.is_connected

    async def connect(self) -> bool:
        """Connect to Google Drive API."""
        return await self.server.ensure_connected()

    def list_files(
        self, folder_id: str = "", query: str = ""
    ) -> dict[str, Any]:
        """List files in a Drive folder."""
        return self.server._list_files(folder_id=folder_id, query=query)

    def get_file_content(self, file_id: str) -> dict[str, Any]:
        """Get a single file's text content."""
        return self.server._get_file_content(file_id)

    def sync_folder(
        self, folder_id: str, subject: str = ""
    ) -> dict[str, Any]:
        """Sync all files from a folder into ChromaDB."""
        return self.server._sync_folder(folder_id=folder_id, subject=subject)

    def sync_selected_files(
        self, file_ids: list[str], subject: str = ""
    ) -> dict[str, Any]:
        """Sync only selected files into ChromaDB."""
        return self.server._sync_selected_files(
            file_ids=file_ids, subject=subject
        )


# Module-level singleton
gdrive_service = GoogleDriveService()
