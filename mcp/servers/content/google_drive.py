"""
MCP Server -- Google Drive.

Acces aux documents partages (slides, annales, PDF).
Synchronise les fichiers d'un dossier Drive vers ChromaDB.

Requires: pip install google-api-python-client google-auth
"""

from __future__ import annotations

import io
import logging
import tempfile
from pathlib import Path
from typing import Any

from mcp.base import BaseMCPServer, MCPToolDefinition, MCPStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependencies
# ---------------------------------------------------------------------------

try:
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials
    from googleapiclient.discovery import build as build_service
    from googleapiclient.http import MediaIoBaseDownload

    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False

# ---------------------------------------------------------------------------
# MIME type helpers
# ---------------------------------------------------------------------------

EXPORTABLE_MIMES: dict[str, str] = {
    "application/vnd.google-apps.document": "text/plain",
    "application/vnd.google-apps.presentation": "text/plain",
    "application/vnd.google-apps.spreadsheet": "text/csv",
}

DOWNLOADABLE_MIMES: set[str] = {
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

MIME_ICONS: dict[str, str] = {
    "application/pdf": "PDF",
    "application/vnd.google-apps.document": "Doc",
    "application/vnd.google-apps.presentation": "Slides",
    "application/vnd.google-apps.spreadsheet": "Sheet",
    "text/plain": "TXT",
    "text/csv": "CSV",
    "application/vnd.google-apps.folder": "Folder",
}

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------


class GoogleDriveServer(BaseMCPServer):
    SERVER_ID = "google-drive"
    SERVER_NAME = "Google Drive"
    CATEGORY = "content"
    DESCRIPTION = "Acces aux documents partages (slides, annales, PDF)"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._service: Any = None  # googleapiclient Resource

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="list_files",
                description="Lister les fichiers d'un dossier Drive",
                parameters={"folder_id": "str", "query": "str"},
            ),
            MCPToolDefinition(
                name="get_file_content",
                description="Telecharger et extraire le texte d'un fichier",
                parameters={"file_id": "str"},
                required_params=["file_id"],
            ),
            MCPToolDefinition(
                name="sync_folder",
                description="Synchroniser un dossier Drive vers ChromaDB",
                parameters={"folder_id": "str", "subject": "str"},
                required_params=["folder_id"],
            ),
        ]

    # -- Connection ---------------------------------------------------------

    async def connect(self) -> bool:
        if not GDRIVE_AVAILABLE:
            self.logger.warning(
                "google-api-python-client non installe — "
                "run: pip install google-api-python-client google-auth"
            )
            return False

        creds_path = self.config.get(
            "credentials_path", "./credentials/gdrive_service_account.json"
        )
        creds_file = Path(creds_path)
        if not creds_file.exists():
            self.logger.warning("Service account file not found: %s", creds_file)
            return False

        try:
            creds = ServiceAccountCredentials.from_service_account_file(
                str(creds_file), scopes=SCOPES
            )
            self._service = build_service("drive", "v3", credentials=creds)
            # Quick health check
            self._service.about().get(fields="user").execute()
            self._status = MCPStatus.CONNECTED
            self.logger.info("Google Drive server connected")
            return True
        except Exception as exc:
            self.logger.error("Google Drive connection failed: %s", exc)
            self._service = None
            return False

    async def disconnect(self) -> None:
        self._service = None
        self._status = MCPStatus.DISCONNECTED

    async def health(self) -> bool:
        if not self._service:
            return False
        try:
            self._service.about().get(fields="user").execute()
            return True
        except Exception:
            return False

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> Any:
        if tool_name == "list_files":
            return self._list_files(**kwargs)
        elif tool_name == "get_file_content":
            return self._get_file_content(**kwargs)
        elif tool_name == "sync_folder":
            return self._sync_folder(**kwargs)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    # -- Property -----------------------------------------------------------

    @property
    def service(self) -> Any:
        if self._service is None:
            raise RuntimeError("Google Drive not connected")
        return self._service

    # -- Tool implementations -----------------------------------------------

    def _list_files(
        self, folder_id: str = "", query: str = ""
    ) -> dict[str, Any]:
        """List files in a Drive folder."""
        q_parts: list[str] = []
        if folder_id:
            q_parts.append(f"'{folder_id}' in parents")
        q_parts.append("trashed = false")
        if query:
            q_parts.append(f"name contains '{query}'")

        q = " and ".join(q_parts)

        results = (
            self.service.files()
            .list(
                q=q,
                pageSize=100,
                fields="files(id, name, mimeType, size, modifiedTime, webViewLink)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )

        files = []
        for f in results.get("files", []):
            mime = f.get("mimeType", "")
            files.append({
                "id": f["id"],
                "name": f["name"],
                "mimeType": mime,
                "type_label": MIME_ICONS.get(mime, "File"),
                "size": int(f.get("size", 0)),
                "modifiedTime": f.get("modifiedTime", ""),
                "webViewLink": f.get("webViewLink", ""),
            })

        return {"files": files, "total": len(files)}

    def _get_file_content(self, file_id: str) -> dict[str, Any]:
        """Download a file and extract its text content."""
        meta = (
            self.service.files()
            .get(fileId=file_id, fields="id, name, mimeType, size")
            .execute()
        )
        mime = meta.get("mimeType", "")
        name = meta.get("name", "")

        text = self._extract_text(file_id, mime)

        return {
            "id": file_id,
            "name": name,
            "mimeType": mime,
            "content": text,
            "content_length": len(text),
        }

    def _sync_folder(
        self, folder_id: str, subject: str = ""
    ) -> dict[str, Any]:
        """Sync all supported files from a folder into ChromaDB."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_core.documents import Document as LCDoc
        from api.services.rag import rag_service
        from core.config import CHUNK_SIZE, CHUNK_OVERLAP
        from core.constants import (
            META_MATIERE, META_DOC_TYPE, META_FILENAME, META_FILEPATH,
        )

        listing = self._list_files(folder_id=folder_id)
        files = listing["files"]

        if not subject:
            subject = "Google Drive"

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        total_chunks = 0
        synced_files = 0

        for f in files:
            mime = f["mimeType"]
            # Skip folders and unsupported types
            if mime == "application/vnd.google-apps.folder":
                continue
            if mime not in EXPORTABLE_MIMES and mime not in DOWNLOADABLE_MIMES:
                continue

            try:
                text = self._extract_text(f["id"], mime)
            except Exception as exc:
                self.logger.warning(
                    "Failed to extract text from %s (%s): %s",
                    f["name"], f["id"], exc,
                )
                continue

            if len(text) < 50:
                continue

            doc = LCDoc(
                page_content=text,
                metadata={
                    META_MATIERE: subject,
                    META_DOC_TYPE: f.get("type_label", "Document"),
                    META_FILENAME: f["name"],
                    META_FILEPATH: f.get("webViewLink", ""),
                    "source_type": "google_drive",
                    "gdrive_file_id": f["id"],
                },
            )

            chunks = splitter.split_documents([doc])
            rag_service.vectorstore.add_documents(chunks)
            total_chunks += len(chunks)
            synced_files += 1

        # Invalidate BM25 index so new docs are picked up
        if total_chunks:
            rag_service._bm25_index = None

        return {
            "synced_files": synced_files,
            "total_files": len(files),
            "total_chunks": total_chunks,
            "subject": subject,
        }

    def _sync_selected_files(
        self, file_ids: list[str], subject: str = ""
    ) -> dict[str, Any]:
        """Sync only selected files into ChromaDB."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_core.documents import Document as LCDoc
        from api.services.rag import rag_service
        from core.config import CHUNK_SIZE, CHUNK_OVERLAP
        from core.constants import (
            META_MATIERE, META_DOC_TYPE, META_FILENAME, META_FILEPATH,
        )

        if not subject:
            subject = "Google Drive"

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        total_chunks = 0
        synced_files = 0

        for file_id in file_ids:
            try:
                meta = (
                    self.service.files()
                    .get(fileId=file_id, fields="id, name, mimeType, webViewLink")
                    .execute()
                )
            except Exception as exc:
                self.logger.warning("Cannot access file %s: %s", file_id, exc)
                continue

            mime = meta.get("mimeType", "")
            name = meta.get("name", "")

            if mime == "application/vnd.google-apps.folder":
                continue
            if mime not in EXPORTABLE_MIMES and mime not in DOWNLOADABLE_MIMES:
                continue

            try:
                text = self._extract_text(file_id, mime)
            except Exception as exc:
                self.logger.warning(
                    "Failed to extract text from %s: %s", name, exc
                )
                continue

            if len(text) < 50:
                continue

            doc = LCDoc(
                page_content=text,
                metadata={
                    META_MATIERE: subject,
                    META_DOC_TYPE: MIME_ICONS.get(mime, "Document"),
                    META_FILENAME: name,
                    META_FILEPATH: meta.get("webViewLink", ""),
                    "source_type": "google_drive",
                    "gdrive_file_id": file_id,
                },
            )

            chunks = splitter.split_documents([doc])
            rag_service.vectorstore.add_documents(chunks)
            total_chunks += len(chunks)
            synced_files += 1

        if total_chunks:
            rag_service._bm25_index = None

        return {
            "synced_files": synced_files,
            "total_chunks": total_chunks,
            "subject": subject,
        }

    # -- Text extraction ----------------------------------------------------

    def _extract_text(self, file_id: str, mime_type: str) -> str:
        """Extract text from a Drive file based on its MIME type."""
        # Google Workspace files: export as text
        if mime_type in EXPORTABLE_MIMES:
            export_mime = EXPORTABLE_MIMES[mime_type]
            request = self.service.files().export_media(
                fileId=file_id, mimeType=export_mime
            )
            buf = io.BytesIO()
            downloader = MediaIoBaseDownload(buf, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return buf.getvalue().decode("utf-8", errors="replace")

        # PDF: download then extract with PyPDFLoader
        if mime_type == "application/pdf":
            return self._extract_pdf(file_id)

        # Plain text / CSV: download directly
        if mime_type in ("text/plain", "text/csv"):
            request = self.service.files().get_media(fileId=file_id)
            buf = io.BytesIO()
            downloader = MediaIoBaseDownload(buf, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return buf.getvalue().decode("utf-8", errors="replace")

        return ""

    def _extract_pdf(self, file_id: str) -> str:
        """Download a PDF and extract text using PyPDFLoader."""
        from langchain_community.document_loaders import PyPDFLoader

        request = self.service.files().get_media(fileId=file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(buf.getvalue())
            tmp_path = tmp.name

        try:
            loader = PyPDFLoader(tmp_path)
            pages = loader.load()
            return "\n\n".join(p.page_content for p in pages)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
