"""
MCP Server -- OCR (Tesseract).

Extraire du texte depuis images / notes manuscrites.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class OCRServer(BaseMCPServer):
    SERVER_ID = "ocr"
    SERVER_NAME = "OCR"
    CATEGORY = "media"
    DESCRIPTION = "Extraire du texte depuis images et notes manuscrites"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="extract_text",
                description="Extraire le texte d'une image via OCR",
                parameters={"image_path": "str", "language": "str"},
                required_params=["image_path"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("OCR -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
