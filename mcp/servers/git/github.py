"""
MCP Server -- GitHub.

Acces aux repos de code (TPs, projets), indexation README + code.
"""

from __future__ import annotations

from mcp.base import BaseMCPServer, MCPToolDefinition


class GitHubServer(BaseMCPServer):
    SERVER_ID = "github"
    SERVER_NAME = "GitHub"
    CATEGORY = "git"
    DESCRIPTION = "Acces aux repos de code (TPs, projets)"

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="list_repos",
                description="Lister les repositories",
                parameters={"user": "str", "visibility": "str"},
            ),
            MCPToolDefinition(
                name="get_file",
                description="Recuperer un fichier depuis un repo",
                parameters={"repo": "str", "path": "str", "branch": "str"},
                required_params=["repo", "path"],
            ),
            MCPToolDefinition(
                name="search_code",
                description="Rechercher du code dans les repos",
                parameters={"query": "str", "repo": "str"},
                required_params=["query"],
            ),
        ]

    async def connect(self) -> bool:
        self.logger.info("GitHub -- not yet implemented")
        return False

    async def disconnect(self) -> None:
        pass

    async def health(self) -> bool:
        return self.is_connected
