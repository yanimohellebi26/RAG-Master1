"""
MCP Auto-discovery -- Enregistrement automatique de tous les serveurs.

Import ce module pour enregistrer tous les serveurs MCP dans le registre.
"""

from mcp.registry import mcp_registry

# -- Outils personnels -----------------------------------------------------
from mcp.servers.personal.gmail import GmailServer
from mcp.servers.personal.terminal import TerminalServer
from mcp.servers.personal.canva import CanvaServer

# -- Acquisition de contenu ------------------------------------------------
from mcp.servers.content.youtube_transcript import YouTubeTranscriptServer
from mcp.servers.content.notion import NotionServer
from mcp.servers.content.google_drive import GoogleDriveServer
from mcp.servers.content.browser import BrowserServer
from mcp.servers.content.filesystem import FilesystemServer

# -- Recherche et veille ----------------------------------------------------
from mcp.servers.search.brave_search import BraveSearchServer
from mcp.servers.search.exa import ExaServer
from mcp.servers.search.arxiv import ArxivServer
from mcp.servers.search.semantic_scholar import SemanticScholarServer
from mcp.servers.search.wikipedia import WikipediaServer

# -- Images et media --------------------------------------------------------
from mcp.servers.media.vision import VisionServer
from mcp.servers.media.ocr import OCRServer
from mcp.servers.media.dalle import DalleServer
from mcp.servers.media.tts import TTSServer

# -- Code et execution ------------------------------------------------------
from mcp.servers.code.code_interpreter import CodeInterpreterServer
from mcp.servers.code.docker import DockerServer
from mcp.servers.code.jupyter import JupyterServer

# -- Organisation -----------------------------------------------------------
from mcp.servers.organization.google_calendar import GoogleCalendarServer
from mcp.servers.organization.todoist import TodoistServer

# -- Communication ----------------------------------------------------------
from mcp.servers.communication.discord import DiscordServer
from mcp.servers.communication.slack import SlackServer

# -- Memoire et donnees -----------------------------------------------------
from mcp.servers.memory.memory import MemoryServer
from mcp.servers.memory.sqlite import SQLiteServer
from mcp.servers.memory.qdrant import QdrantServer

# -- Git --------------------------------------------------------------------
from mcp.servers.git.github import GitHubServer


# ---------------------------------------------------------------------------
# Enregistrement de tous les serveurs
# ---------------------------------------------------------------------------

ALL_SERVERS = [
    # Outils personnels (priorite haute)
    GmailServer,
    TerminalServer,
    CanvaServer,
    # Acquisition de contenu
    YouTubeTranscriptServer,
    NotionServer,
    GoogleDriveServer,
    BrowserServer,
    FilesystemServer,
    # Recherche et veille
    BraveSearchServer,
    ExaServer,
    ArxivServer,
    SemanticScholarServer,
    WikipediaServer,
    # Images et media
    VisionServer,
    OCRServer,
    DalleServer,
    TTSServer,
    # Code et execution
    CodeInterpreterServer,
    DockerServer,
    JupyterServer,
    # Organisation
    GoogleCalendarServer,
    TodoistServer,
    # Communication
    DiscordServer,
    SlackServer,
    # Memoire et donnees
    MemoryServer,
    SQLiteServer,
    QdrantServer,
    # Git
    GitHubServer,
]


def register_all() -> None:
    """Enregistrer tous les serveurs MCP dans le registre global."""
    for server_class in ALL_SERVERS:
        mcp_registry.register(server_class)


# Auto-register on import
register_all()
