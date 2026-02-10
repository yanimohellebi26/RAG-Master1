"""
MCP Server -- Google Calendar.

Planning de revision et rappels avant examens.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class GoogleCalendarServer(BaseMCPServer):
    SERVER_ID = "google-calendar"
    SERVER_NAME = "Google Calendar"
    CATEGORY = "organization"
    DESCRIPTION = "Planning de revision et rappels avant examens"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="list_events",
                description="Lister les evenements a venir",
                parameters={"days_ahead": "int", "calendar_id": "str"},
            ),
            MCPToolDefinition(
                name="create_event",
                description="Creer un evenement de revision",
                parameters={
                    "title": "str", "start": "str", "end": "str",
                    "description": "str",
                },
                required_params=["title", "start", "end"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("Google Calendar -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
