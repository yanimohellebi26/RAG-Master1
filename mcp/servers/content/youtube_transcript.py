"""
MCP Server -- YouTube Transcript.

Transcrire les cours video YouTube et les indexer dans ChromaDB.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class YouTubeTranscriptServer(BaseMCPServer):
    SERVER_ID = "youtube-transcript"
    SERVER_NAME = "YouTube Transcript"
    CATEGORY = "content"
    DESCRIPTION = "Transcrire les cours video YouTube et les indexer"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="get_transcript",
                description="Recuperer la transcription d'une video YouTube",
                parameters={"video_url": "str", "language": "str"},
                required_params=["video_url"],
            ),
            MCPToolDefinition(
                name="index_transcript",
                description="Indexer une transcription dans ChromaDB",
                parameters={"video_url": "str", "subject": "str"},
                required_params=["video_url"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("YouTube Transcript -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
