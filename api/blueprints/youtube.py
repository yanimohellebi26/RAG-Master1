"""
YouTube Blueprint -- /api/youtube/* routes.

Endpoints :
    POST /api/youtube/transcript     -- Recuperer la transcription brute
    POST /api/youtube/index          -- Indexer dans ChromaDB
    POST /api/youtube/analyze        -- Analyse IA (non-streaming)
    POST /api/youtube/analyze/stream -- Analyse IA (SSE streaming)
    GET  /api/youtube/status         -- Statut du service
"""

import json
import logging
from flask import Blueprint, Response, jsonify, request, stream_with_context

from api.services.youtube import youtube_service

logger = logging.getLogger(__name__)
youtube_bp = Blueprint("youtube", __name__)


@youtube_bp.route("/youtube/status", methods=["GET"])
def youtube_status():
    """Check if youtube-transcript-api is available."""
    return jsonify({
        "available": youtube_service.available,
        "message": (
            "youtube-transcript-api installé et prêt"
            if youtube_service.available
            else "youtube-transcript-api non installé. Run: pip install youtube-transcript-api"
        ),
    })


@youtube_bp.route("/youtube/transcript", methods=["POST"])
def get_transcript():
    """Fetch a cleaned transcript for a YouTube video."""
    data = request.get_json()
    if not data or not data.get("video_url"):
        return jsonify({"error": "video_url is required"}), 400

    try:
        result = youtube_service.get_transcript(
            video_url=data["video_url"],
            languages=data.get("languages"),
        )
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.error("Transcript fetch failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@youtube_bp.route("/youtube/index", methods=["POST"])
def index_transcript():
    """Index a YouTube transcript into ChromaDB."""
    data = request.get_json()
    if not data or not data.get("video_url"):
        return jsonify({"error": "video_url is required"}), 400
    if not data.get("subject"):
        return jsonify({"error": "subject is required"}), 400

    try:
        result = youtube_service.index_transcript(
            video_url=data["video_url"],
            subject=data["subject"],
            doc_type=data.get("doc_type", "Video"),
        )
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.error("Transcript indexation failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@youtube_bp.route("/youtube/analyze", methods=["POST"])
def analyze_video():
    """Run AI analysis on a YouTube video (non-streaming)."""
    data = request.get_json()
    if not data or not data.get("video_url"):
        return jsonify({"error": "video_url is required"}), 400

    try:
        result = youtube_service.analyze_video(
            video_url=data["video_url"],
            analysis_type=data.get("analysis_type", "all"),
        )
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.error("Video analysis failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@youtube_bp.route("/youtube/analyze/stream", methods=["POST"])
def analyze_video_stream():
    """Stream AI analysis on a YouTube video via SSE."""
    data = request.get_json()
    if not data or not data.get("video_url"):
        return jsonify({"error": "video_url is required"}), 400

    video_url = data["video_url"]
    analysis_type = data.get("analysis_type", "summary")

    def generate():
        try:
            for event in youtube_service.analyze_video_stream(video_url, analysis_type):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except ValueError as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"
        except Exception as exc:
            logger.error("Stream analysis failed: %s", exc)
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@youtube_bp.route("/youtube/search", methods=["POST"])
def search_videos():
    """Search YouTube for explanatory videos related to a course concept."""
    data = request.get_json()
    if not data or not data.get("concept"):
        return jsonify({"error": "concept is required"}), 400

    try:
        result = youtube_service.search_videos(
            concept=data["concept"],
            context=data.get("context", ""),
            max_results=data.get("max_results", 5),
        )
        return jsonify(result)
    except Exception as exc:
        logger.error("Video search failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@youtube_bp.route("/youtube/history", methods=["GET"])
def get_indexed_videos():
    """Get all YouTube videos indexed in ChromaDB."""
    subject = request.args.get("subject")
    try:
        videos = youtube_service.get_indexed_videos(subject=subject or None)
        return jsonify({"videos": videos, "total": len(videos)})
    except Exception as exc:
        logger.error("Failed to fetch indexed videos: %s", exc)
        return jsonify({"error": str(exc)}), 500


@youtube_bp.route("/youtube/history/<video_id>", methods=["DELETE"])
def delete_indexed_video(video_id):
    """Delete an indexed YouTube video from ChromaDB."""
    try:
        result = youtube_service.delete_indexed_video(video_id)
        return jsonify(result)
    except Exception as exc:
        logger.error("Failed to delete video %s: %s", video_id, exc)
        return jsonify({"error": str(exc)}), 500
