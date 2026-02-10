"""
MCP Server -- Browser / Puppeteer.

Scraper les pages de cours en ligne (Moodle, sites de profs).
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class BrowserServer(BaseMCPServer):
    SERVER_ID = "browser"
    SERVER_NAME = "Browser"
    CATEGORY = "content"
    DESCRIPTION = "Scraper les pages de cours en ligne (Moodle, sites de profs)"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="fetch_page",
                description="Recuperer le contenu d'une page web",
                parameters={"url": "str", "selector": "str"},
                required_params=["url"],
            ),
            MCPToolDefinition(
                name="screenshot",
                description="Capture ecran d'une page web",
                parameters={"url": "str", "output_path": "str"},
                required_params=["url"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Browser/Puppeteer -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
