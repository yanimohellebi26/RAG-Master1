"""
MCP API Blueprint -- Endpoints pour gerer les serveurs MCP.

Routes :
    GET  /api/mcp/servers          -- Liste de tous les serveurs MCP
    GET  /api/mcp/servers/<id>     -- Details d'un serveur
    GET  /api/mcp/categories       -- Liste des categories
    POST /api/mcp/servers/<id>/connect    -- Connecter un serveur
    POST /api/mcp/servers/<id>/disconnect -- Deconnecter un serveur
    POST /api/mcp/servers/<id>/tool       -- Executer un outil
    GET  /api/mcp/stats            -- Statistiques du registre
"""

from __future__ import annotations

import asyncio
import logging
from flask import Blueprint, jsonify, request

from mcp.registry import mcp_registry

logger = logging.getLogger(__name__)
mcp_bp = Blueprint("mcp", __name__)


def _run_async(coro):
    """Helper pour executer une coroutine async depuis Flask (sync)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@mcp_bp.route("/mcp/servers", methods=["GET"])
def list_servers():
    """Liste de tous les serveurs MCP avec leur statut."""
    category = request.args.get("category")
    if category:
        servers = mcp_registry.list_by_category(category)
    else:
        servers = mcp_registry.list_servers()
    return jsonify({"servers": servers, "stats": mcp_registry.stats})


@mcp_bp.route("/mcp/servers/<server_id>", methods=["GET"])
def get_server(server_id: str):
    """Details d'un serveur MCP specifique."""
    server = mcp_registry.get(server_id)
    if not server:
        return jsonify({"error": f"Server '{server_id}' not found"}), 404
    return jsonify(server.info.to_dict())


@mcp_bp.route("/mcp/categories", methods=["GET"])
def list_categories():
    """Liste des categories MCP avec le nombre de serveurs."""
    servers = mcp_registry.list_servers()
    categories: dict[str, int] = {}
    for s in servers:
        cat = s["category"]
        categories[cat] = categories.get(cat, 0) + 1
    return jsonify({"categories": categories})


@mcp_bp.route("/mcp/servers/<server_id>/connect", methods=["POST"])
def connect_server(server_id: str):
    """Connecter un serveur MCP."""
    server = mcp_registry.get(server_id)
    if not server:
        return jsonify({"error": f"Server '{server_id}' not found"}), 404
    success = _run_async(server.ensure_connected())
    return jsonify({
        "server_id": server_id,
        "connected": success,
        "status": server.status.value,
    })


@mcp_bp.route("/mcp/servers/<server_id>/disconnect", methods=["POST"])
def disconnect_server(server_id: str):
    """Deconnecter un serveur MCP."""
    server = mcp_registry.get(server_id)
    if not server:
        return jsonify({"error": f"Server '{server_id}' not found"}), 404
    _run_async(server.safe_disconnect())
    return jsonify({
        "server_id": server_id,
        "status": server.status.value,
    })


@mcp_bp.route("/mcp/servers/<server_id>/tool", methods=["POST"])
def execute_tool(server_id: str):
    """Executer un outil d'un serveur MCP."""
    server = mcp_registry.get(server_id)
    if not server:
        return jsonify({"error": f"Server '{server_id}' not found"}), 404

    if not server.is_connected:
        return jsonify({"error": f"Server '{server_id}' is not connected"}), 400

    data = request.get_json() or {}
    tool_name = data.get("tool")
    params = data.get("params", {})

    if not tool_name:
        return jsonify({"error": "Missing 'tool' in request body"}), 400

    try:
        result = _run_async(server.execute_tool(tool_name, **params))
        return jsonify({"result": result})
    except NotImplementedError as exc:
        return jsonify({"error": str(exc)}), 501
    except Exception as exc:
        logger.error(f"Tool execution error: {exc}")
        return jsonify({"error": str(exc)}), 500


@mcp_bp.route("/mcp/stats", methods=["GET"])
def mcp_stats():
    """Statistiques globales du registre MCP."""
    return jsonify(mcp_registry.stats)
