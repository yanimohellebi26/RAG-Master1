"""
MCP Server -- Notion.

Connecter les notes personnelles Notion comme source de connaissances.
Permet aussi de sauvegarder des syntheses de chat vers Notion.

Requires: pip install notion-client
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.base import BaseMCPServer, MCPToolDefinition, MCPStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency
# ---------------------------------------------------------------------------

try:
    from notion_client import Client as NotionClient

    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False

# ---------------------------------------------------------------------------
# Subject -> Notion tag mapping
# ---------------------------------------------------------------------------

DEFAULT_SUBJECT_TAG_MAP: dict[str, str] = {
    "Algorithmique": "Algo",
    "Analyse Exploratoire de Donnees": "AnalyseExplo",
    "Cloud & Reseaux": "Cloud",
    "Conception Web Avancee": "CWA",
    "Genie Logiciel": "GenieLog",
    "Intelligence Artificielle": "IA",
    "Logique & Prolog": "Logique",
    "SGBD Graphes": "SGBDGraphes",
    "Systemes de Gestion de Donnees": "SGD",
    "Systemes Distribues": "SystDistri",
}


def map_subject_to_tag(subject: str) -> str:
    """Map a full subject name to a short Notion tag."""
    return DEFAULT_SUBJECT_TAG_MAP.get(subject, subject)


def map_tag_to_subject(tag: str) -> str:
    """Map a short tag back to the full subject name."""
    reverse = {v: k for k, v in DEFAULT_SUBJECT_TAG_MAP.items()}
    return reverse.get(tag, tag)


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------


class NotionServer(BaseMCPServer):
    SERVER_ID = "notion"
    SERVER_NAME = "Notion"
    CATEGORY = "content"
    DESCRIPTION = "Connecter les notes personnelles Notion comme source"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._client: NotionClient | None = None
        self._access_token: str = ""

    def set_access_token(self, token: str) -> None:
        """Set an OAuth access token (used by OAuth flow)."""
        self._access_token = token

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="search_pages",
                description="Rechercher dans les pages Notion",
                parameters={"query": "str"},
                required_params=["query"],
            ),
            MCPToolDefinition(
                name="get_page",
                description="Recuperer le contenu d'une page Notion",
                parameters={"page_id": "str"},
                required_params=["page_id"],
            ),
            MCPToolDefinition(
                name="sync_pages",
                description="Synchroniser les pages Notion vers ChromaDB",
                parameters={"database_id": "str"},
            ),
            MCPToolDefinition(
                name="create_page",
                description="Creer une page de synthese dans Notion",
                parameters={
                    "title": "str",
                    "content_markdown": "str",
                    "tags": "list[str]",
                    "database_id": "str (optional)",
                },
                required_params=["title", "content_markdown"],
            ),
        ]

    async def connect(self) -> bool:
        import os

        if not NOTION_AVAILABLE:
            self.logger.warning(
                "notion-client not installed — run: pip install notion-client"
            )
            return False

        api_key = (
            self._access_token
            or os.getenv("NOTION_API_KEY")
            or self.config.get("api_key")
            or ""
        )
        if not api_key:
            self.logger.warning("Notion API key / OAuth token not configured")
            return False

        try:
            self._client = NotionClient(auth=api_key)
            # Quick health check
            self._client.users.me()
            self._status = MCPStatus.CONNECTED
            self.logger.info("Notion server connected")
            return True
        except Exception as exc:
            self.logger.error(f"Notion connection failed: {exc}")
            self._client = None
            return False

    async def disconnect(self) -> None:
        self._client = None
        self._status = MCPStatus.DISCONNECTED

    async def health(self) -> bool:
        if not self._client:
            return False
        try:
            self._client.users.me()
            return True
        except Exception:
            return False

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> Any:
        if tool_name == "search_pages":
            return self._search_pages(**kwargs)
        elif tool_name == "get_page":
            return self._get_page(**kwargs)
        elif tool_name == "sync_pages":
            return self._sync_pages(**kwargs)
        elif tool_name == "create_page":
            return self._create_page(**kwargs)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    # -- Tool implementations -----------------------------------------------

    @property
    def client(self) -> NotionClient:
        if self._client is None:
            raise RuntimeError("Notion not connected")
        return self._client

    def _search_pages(self, query: str) -> dict[str, Any]:
        """Search Notion pages matching a query."""
        response = self.client.search(
            query=query,
            filter={"property": "object", "value": "page"},
            page_size=10,
        )
        pages = []
        for result in response.get("results", []):
            title = _extract_title(result)
            pages.append({
                "id": result["id"],
                "title": title,
                "url": result.get("url", ""),
                "created_time": result.get("created_time", ""),
                "last_edited_time": result.get("last_edited_time", ""),
            })
        return {"pages": pages, "total": len(pages)}

    def _get_page(self, page_id: str) -> dict[str, Any]:
        """Get page content as plain text."""
        page = self.client.pages.retrieve(page_id)
        title = _extract_title(page)

        # Fetch blocks (page content)
        blocks = self.client.blocks.children.list(page_id)
        text_parts: list[str] = []
        for block in blocks.get("results", []):
            text = _extract_block_text(block)
            if text:
                text_parts.append(text)

        return {
            "id": page_id,
            "title": title,
            "content": "\n\n".join(text_parts),
            "url": page.get("url", ""),
        }

    def _sync_pages(self, database_id: str = "") -> dict[str, Any]:
        """Sync Notion pages into ChromaDB for RAG retrieval."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_core.documents import Document as LCDoc
        from api.services.rag import rag_service
        from core.config import CHUNK_SIZE, CHUNK_OVERLAP
        from core.constants import (
            META_MATIERE, META_DOC_TYPE, META_FILENAME, META_FILEPATH,
        )

        # Get pages from database or search all
        if database_id:
            response = self.client.databases.query(database_id=database_id)
        else:
            response = self.client.search(
                filter={"property": "object", "value": "page"},
                page_size=50,
            )

        pages = response.get("results", [])
        total_chunks = 0

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        for page in pages:
            page_id = page["id"]
            title = _extract_title(page)

            # Fetch content
            blocks = self.client.blocks.children.list(page_id)
            text_parts = []
            for block in blocks.get("results", []):
                text = _extract_block_text(block)
                if text:
                    text_parts.append(text)

            full_text = "\n\n".join(text_parts)
            if len(full_text) < 50:
                continue

            # Try to detect subject from tags
            tags = _extract_tags(page)
            subject = "Notion"
            for tag in tags:
                mapped = map_tag_to_subject(tag)
                if mapped != tag:
                    subject = mapped
                    break

            doc = LCDoc(
                page_content=full_text,
                metadata={
                    META_MATIERE: subject,
                    META_DOC_TYPE: "Note Notion",
                    META_FILENAME: f"notion_{title}.md",
                    META_FILEPATH: page.get("url", ""),
                    "source_type": "notion",
                    "notion_page_id": page_id,
                    "notion_title": title,
                },
            )

            chunks = splitter.split_documents([doc])
            rag_service.vectorstore.add_documents(chunks)
            total_chunks += len(chunks)

        if total_chunks:
            rag_service._bm25_index = None

        return {
            "synced_pages": len(pages),
            "total_chunks": total_chunks,
        }

    _rag_folder_id: str = ""

    def _find_parent_page(self) -> str:
        """Find a shared page to use as parent for new pages (OAuth flow)."""
        response = self.client.search(
            filter={"property": "object", "value": "page"},
            page_size=1,
        )
        results = response.get("results", [])
        if results:
            return results[0]["id"]

        raise RuntimeError(
            "Aucune page Notion partagee trouvee. "
            "Dans Notion, ouvrez une page > ... > Connect to > selectionnez votre integration."
        )

    def _get_or_create_rag_folder(self) -> str:
        """
        Find or create the 'Notes Assistant RAG M1' folder page.
        Caches the ID to avoid repeated lookups.
        """
        if self._rag_folder_id:
            return self._rag_folder_id

        folder_name = self.config.get("folder_name", "Notes Assistant RAG M1")

        # Search for existing folder
        response = self.client.search(
            query=folder_name,
            filter={"property": "object", "value": "page"},
            page_size=5,
        )
        for result in response.get("results", []):
            if _extract_title(result) == folder_name:
                self._rag_folder_id = result["id"]
                self.logger.info("Found RAG folder: %s", self._rag_folder_id)
                return self._rag_folder_id

        # Not found — create it under a shared parent
        parent_id = self.config.get("parent_page_id", "") or self._find_parent_page()
        folder = self.client.pages.create(
            parent={"page_id": parent_id},
            properties={
                "title": [{"text": {"content": folder_name}}],
            },
            children=[
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [{"type": "text", "text": {"content":
                            "Dossier auto-genere par l'Assistant RAG M1. "
                            "Les syntheses de vos conversations sont sauvegardees ici."
                        }}],
                        "icon": {"type": "emoji", "emoji": "📚"},
                    },
                },
            ],
        )
        self._rag_folder_id = folder["id"]
        self.logger.info("Created RAG folder: %s", self._rag_folder_id)
        return self._rag_folder_id

    def _create_page(
        self,
        title: str,
        content_markdown: str,
        tags: list[str] | None = None,
        database_id: str = "",
    ) -> dict[str, Any]:
        """Create a new page in Notion inside the RAG folder."""
        target_db = database_id or self.config.get("database_id", "")

        # Build Notion blocks from markdown
        blocks = _markdown_to_notion_blocks(content_markdown)

        if target_db:
            properties: dict[str, Any] = {
                "Name": {"title": [{"text": {"content": title}}]},
            }
            if tags:
                properties["Tags"] = {
                    "multi_select": [{"name": tag} for tag in tags],
                }
            page = self.client.pages.create(
                parent={"database_id": target_db},
                properties=properties,
                children=blocks,
            )
        else:
            # Always create inside the RAG folder
            folder_id = self._get_or_create_rag_folder()
            page = self.client.pages.create(
                parent={"page_id": folder_id},
                properties={
                    "title": [{"text": {"content": title}}],
                },
                children=blocks,
            )

        return {
            "id": page["id"],
            "url": page.get("url", ""),
            "title": title,
        }

    def _sync_selected_pages(self, page_ids: list[str]) -> dict[str, Any]:
        """Sync only the selected pages into ChromaDB."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_core.documents import Document as LCDoc
        from api.services.rag import rag_service
        from core.config import CHUNK_SIZE, CHUNK_OVERLAP
        from core.constants import (
            META_MATIERE, META_DOC_TYPE, META_FILENAME, META_FILEPATH,
        )

        total_chunks = 0
        synced = 0
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        for page_id in page_ids:
            try:
                page = self.client.pages.retrieve(page_id)
            except Exception as exc:
                self.logger.warning("Cannot access page %s: %s", page_id, exc)
                continue

            title = _extract_title(page)
            blocks = self.client.blocks.children.list(page_id)
            text_parts = []
            for block in blocks.get("results", []):
                text = _extract_block_text(block)
                if text:
                    text_parts.append(text)

            full_text = "\n\n".join(text_parts)
            if len(full_text) < 50:
                continue

            tags = _extract_tags(page)
            subject = "Notion"
            for tag in tags:
                mapped = map_tag_to_subject(tag)
                if mapped != tag:
                    subject = mapped
                    break

            doc = LCDoc(
                page_content=full_text,
                metadata={
                    META_MATIERE: subject,
                    META_DOC_TYPE: "Note Notion",
                    META_FILENAME: f"notion_{title}.md",
                    META_FILEPATH: page.get("url", ""),
                    "source_type": "notion",
                    "notion_page_id": page_id,
                    "notion_title": title,
                },
            )

            chunks = splitter.split_documents([doc])
            rag_service.vectorstore.add_documents(chunks)
            total_chunks += len(chunks)
            synced += 1

        if total_chunks:
            rag_service._bm25_index = None

        return {"synced_pages": synced, "total_chunks": total_chunks}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_title(page: dict) -> str:
    """Extract title from a Notion page object."""
    props = page.get("properties", {})
    for prop in props.values():
        if prop.get("type") == "title":
            title_parts = prop.get("title", [])
            return "".join(t.get("plain_text", "") for t in title_parts)
    return "Sans titre"


def _extract_tags(page: dict) -> list[str]:
    """Extract multi_select tags from a Notion page."""
    props = page.get("properties", {})
    for prop in props.values():
        if prop.get("type") == "multi_select":
            return [t.get("name", "") for t in prop.get("multi_select", [])]
    return []


def _extract_block_text(block: dict) -> str:
    """Extract plain text from a Notion block."""
    block_type = block.get("type", "")
    block_data = block.get(block_type, {})

    if "rich_text" in block_data:
        return "".join(
            t.get("plain_text", "") for t in block_data["rich_text"]
        )
    if "text" in block_data:
        return "".join(
            t.get("plain_text", "") for t in block_data["text"]
        )
    return ""


def _markdown_to_notion_blocks(markdown: str) -> list[dict]:
    """Convert simple markdown to Notion block objects."""
    blocks: list[dict] = []
    lines = markdown.split("\n")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("### "):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[4:]}}],
                },
            })
        elif stripped.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[3:]}}],
                },
            })
        elif stripped.startswith("# "):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[2:]}}],
                },
            })
        elif stripped.startswith("- ") or stripped.startswith("* "):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[2:]}}],
                },
            })
        elif stripped.startswith("```"):
            # Skip code fences (simplified)
            continue
        else:
            # Notion API limits rich_text content to 2000 chars per block
            content = stripped[:2000]
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content}}],
                },
            })

    return blocks
