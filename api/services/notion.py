"""
Notion Service -- Interface haut-niveau pour le MCP Notion.

Utilise par le blueprint /api/notion pour exposer les fonctionnalites
sans coupler directement Flask au MCP server.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.servers.content.notion import (
    NotionServer,
    NOTION_AVAILABLE,
    map_subject_to_tag,
)

logger = logging.getLogger(__name__)


class NotionService:
    """Service singleton for Notion operations."""

    def __init__(self) -> None:
        self._server: NotionServer | None = None

    @property
    def available(self) -> bool:
        return NOTION_AVAILABLE

    @property
    def server(self) -> NotionServer:
        if self._server is None:
            from core.config import CONFIG
            mcp_cfg = CONFIG.get("mcp", {}).get("notion", {})
            self._server = NotionServer(config=mcp_cfg)
        return self._server

    @property
    def connected(self) -> bool:
        return self._server is not None and self._server.is_connected

    def set_access_token(self, token: str) -> None:
        """Set the OAuth access token on the server."""
        self.server.set_access_token(token)

    async def connect(self) -> bool:
        """Connect to Notion API."""
        return await self.server.ensure_connected()

    def search_pages(self, query: str) -> dict[str, Any]:
        """Search Notion pages."""
        return self.server._search_pages(query)

    def get_page(self, page_id: str) -> dict[str, Any]:
        """Get a single Notion page content."""
        return self.server._get_page(page_id)

    def save_synthesis(
        self,
        title: str,
        messages: list[dict[str, Any]],
        sources: list[dict[str, Any]] | None = None,
        subjects: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Save a chat synthesis to Notion.

        Builds a structured markdown document from the conversation,
        then creates a Notion page with the content.
        """
        # Build markdown content from messages
        markdown_parts: list[str] = []
        markdown_parts.append(f"# {title}\n")
        markdown_parts.append("## Conversation\n")

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                markdown_parts.append(f"### Question")
                markdown_parts.append(content)
                markdown_parts.append("")
            elif role == "assistant" and content:
                markdown_parts.append(f"### Reponse")
                markdown_parts.append(content)
                markdown_parts.append("")

        # Add sources section
        if sources:
            markdown_parts.append("## Sources utilisees")
            for src in sources:
                if isinstance(src, dict):
                    matiere = src.get("matiere", "")
                    doc_type = src.get("doc_type", "")
                    filename = src.get("filename", "")
                    markdown_parts.append(f"- {matiere} ({doc_type}): {filename}")
                else:
                    markdown_parts.append(f"- {src}")
            markdown_parts.append("")

        content_markdown = "\n".join(markdown_parts)

        # Build tags from subjects
        tags = ["RAG-M1", "Synthese"]
        if subjects:
            for subject in subjects:
                tag = map_subject_to_tag(subject)
                if tag not in tags:
                    tags.append(tag)

        return self.server._create_page(
            title=title,
            content_markdown=content_markdown,
            tags=tags,
        )

    def list_pages(self, query: str = " ") -> list[dict[str, Any]]:
        """List available Notion pages for selective indexation."""
        result = self.server._search_pages(query)
        return result.get("pages", [])

    def sync_pages(self, database_id: str = "") -> dict[str, Any]:
        """Sync all Notion pages into ChromaDB."""
        return self.server._sync_pages(database_id)

    def sync_selected_pages(self, page_ids: list[str]) -> dict[str, Any]:
        """Sync only selected pages into ChromaDB."""
        return self.server._sync_selected_pages(page_ids)


# Module-level singleton
notion_service = NotionService()
