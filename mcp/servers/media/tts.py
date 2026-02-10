"""
MCP Server -- TTS (Text-to-Speech).

Convertir les reponses en audio pour reviser en ecoutant.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class TTSServer(BaseMCPServer):
    SERVER_ID = "tts"
    SERVER_NAME = "Text-to-Speech"
    CATEGORY = "media"
    DESCRIPTION = "Convertir les reponses en audio pour reviser en ecoutant"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="synthesize",
                description="Convertir du texte en audio",
                parameters={"text": "str", "voice": "str", "output_path": "str"},
                required_params=["text"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("TTS -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
