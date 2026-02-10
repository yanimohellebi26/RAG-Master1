"""
YouTube Service -- Interface haut-niveau pour le MCP YouTube Transcript.

Utilise par le blueprint /api/youtube pour exposer les fonctionnalites
sans coupler directement Flask au MCP server.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.servers.content.youtube_transcript import (
    YouTubeTranscriptServer,
    extract_video_id,
    fetch_transcript,
    clean_transcript,
    YT_TRANSCRIPT_AVAILABLE,
)

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service singleton for YouTube transcript operations."""

    def __init__(self) -> None:
        self._server: YouTubeTranscriptServer | None = None

    @property
    def available(self) -> bool:
        return YT_TRANSCRIPT_AVAILABLE

    @property
    def server(self) -> YouTubeTranscriptServer:
        if self._server is None:
            from core.config import CONFIG
            mcp_cfg = CONFIG.get("mcp", {}).get("youtube-transcript", {})
            self._server = YouTubeTranscriptServer(config=mcp_cfg)
        return self._server

    def get_transcript(
        self,
        video_url: str,
        languages: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch and clean a YouTube transcript."""
        video_id = extract_video_id(video_url)
        if not video_id:
            raise ValueError(f"URL YouTube invalide : {video_url}")

        data = fetch_transcript(video_id, languages)
        data["full_text"] = clean_transcript(data["full_text"])
        data["url"] = f"https://www.youtube.com/watch?v={video_id}"
        return data

    def index_transcript(
        self,
        video_url: str,
        subject: str,
        doc_type: str = "Video",
    ) -> dict[str, Any]:
        """Fetch, chunk, index a transcript into ChromaDB."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_core.documents import Document as LCDoc
        from api.services.rag import rag_service
        from core.config import CHUNK_SIZE, CHUNK_OVERLAP
        from core.constants import (
            META_MATIERE, META_DOC_TYPE, META_FILENAME, META_FILEPATH,
        )

        transcript = self.get_transcript(video_url)
        video_id = transcript["video_id"]
        text = transcript["full_text"]

        if not text or len(text) < 50:
            return {
                "indexed": 0,
                "message": "Transcription trop courte ou vide",
            }

        filename = f"youtube_{video_id}.txt"
        doc = LCDoc(
            page_content=text,
            metadata={
                META_MATIERE: subject,
                META_DOC_TYPE: doc_type,
                META_FILENAME: filename,
                META_FILEPATH: f"https://youtube.com/watch?v={video_id}",
                "source_type": "youtube",
                "video_id": video_id,
                "language": transcript["language"],
                "duration_seconds": transcript["duration_seconds"],
            },
        )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_documents([doc])
        rag_service.vectorstore.add_documents(chunks)
        rag_service._bm25_index = None  # Invalidate BM25 cache

        return {
            "indexed": len(chunks),
            "video_id": video_id,
            "subject": subject,
            "doc_type": doc_type,
            "language": transcript["language"],
            "duration_seconds": transcript["duration_seconds"],
            "text_length": len(text),
            "url": transcript["url"],
        }

    def analyze_video(
        self,
        video_url: str,
        analysis_type: str = "all",
    ) -> dict[str, Any]:
        """Fetch transcript and run AI analysis (summary, concepts, detailed)."""
        from api.services.rag import rag_service

        transcript = self.get_transcript(video_url)
        text = transcript["full_text"]

        if not text:
            return {"error": "Transcription vide"}

        max_chars = 12_000
        truncated = text[:max_chars]
        is_truncated = len(text) > max_chars

        prompts = {
            "summary": (
                "Tu es un assistant pedagogique expert. "
                "Fais un resume structure et clair de cette transcription de video YouTube. "
                "Utilise des titres (##), des listes a puces, et mets en avant les points cles.\n\n"
                f"Transcription :\n{truncated}"
            ),
            "concepts": (
                "Tu es un assistant pedagogique expert. "
                "Extrais les concepts cles de cette transcription de video YouTube. "
                "Pour chaque concept, donne une definition courte et un exemple si possible. "
                "Organise par themes.\n\n"
                f"Transcription :\n{truncated}"
            ),
            "detailed": (
                "Tu es un assistant pedagogique expert. "
                "Fais une analyse detaillee de cette transcription de video YouTube :\n"
                "1. Resume en 3-5 phrases\n"
                "2. Concepts cles avec definitions\n"
                "3. Points importants a retenir\n"
                "4. Questions de revision possibles\n"
                "5. Liens avec d'autres sujets\n\n"
                f"Transcription :\n{truncated}"
            ),
        }

        results: dict[str, Any] = {
            "video_id": transcript["video_id"],
            "url": transcript["url"],
            "language": transcript["language"],
            "duration_seconds": transcript["duration_seconds"],
            "transcript_length": len(text),
            "is_truncated": is_truncated,
            "transcript": text,
        }

        if analysis_type == "all":
            types_to_run = ["summary", "concepts", "detailed"]
        elif analysis_type in prompts:
            types_to_run = [analysis_type]
        else:
            types_to_run = ["summary"]

        llm = rag_service.llm
        for atype in types_to_run:
            try:
                response = llm.invoke(prompts[atype])
                results[atype] = response.content
            except Exception as exc:
                logger.error("Analysis '%s' failed: %s", atype, exc)
                results[atype] = f"Erreur lors de l'analyse : {exc}"

        return results

    def analyze_video_stream(
        self,
        video_url: str,
        analysis_type: str = "summary",
    ):
        """
        Generator that yields SSE-style dicts for streaming analysis.
        Yields: {"type": "transcript", ...}, {"type": "token", ...}, {"type": "done"}
        """
        import json
        from api.services.rag import rag_service

        transcript = self.get_transcript(video_url)
        text = transcript["full_text"]

        if not text:
            yield {"type": "error", "message": "Transcription vide"}
            return

        # Send transcript metadata first
        yield {
            "type": "transcript",
            "video_id": transcript["video_id"],
            "url": transcript["url"],
            "language": transcript["language"],
            "duration_seconds": transcript["duration_seconds"],
            "transcript_length": len(text),
            "transcript_preview": text[:500],
        }

        max_chars = 12_000
        truncated = text[:max_chars]

        prompts = {
            "summary": (
                "Tu es un assistant pedagogique expert. "
                "Fais un resume structure et clair de cette transcription de video YouTube. "
                "Utilise des titres (##), des listes a puces, et mets en avant les points cles.\n\n"
                f"Transcription :\n{truncated}"
            ),
            "concepts": (
                "Tu es un assistant pedagogique expert. "
                "Extrais les concepts cles de cette transcription de video YouTube. "
                "Pour chaque concept, donne une definition courte et un exemple si possible. "
                "Organise par themes.\n\n"
                f"Transcription :\n{truncated}"
            ),
            "detailed": (
                "Tu es un assistant pedagogique expert. "
                "Fais une analyse detaillee de cette transcription de video YouTube :\n"
                "1. Resume en 3-5 phrases\n"
                "2. Concepts cles avec definitions\n"
                "3. Points importants a retenir\n"
                "4. Questions de revision possibles\n"
                "5. Liens avec d'autres sujets\n\n"
                f"Transcription :\n{truncated}"
            ),
        }

        prompt = prompts.get(analysis_type, prompts["summary"])
        llm = rag_service.llm

        try:
            for chunk in llm.stream(prompt):
                if chunk.content:
                    yield {"type": "token", "content": chunk.content}
            yield {"type": "done"}
        except Exception as exc:
            logger.error("Streaming analysis failed: %s", exc)
            yield {"type": "error", "message": str(exc)}

    # ------------------------------------------------------------------
    # YouTube Video Search (no AI — direct scraping)
    # ------------------------------------------------------------------

    def get_indexed_videos(
        self,
        subject: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve all YouTube videos that have been indexed into ChromaDB.
        Returns one entry per unique video_id, with aggregated metadata.
        Optionally filter by subject.
        """
        from api.services.rag import rag_service
        from core.constants import META_MATIERE, META_DOC_TYPE, META_FILENAME, META_FILEPATH

        store = rag_service.vectorstore
        result = store.get(include=["metadatas"])

        if not result or not result.get("metadatas"):
            return []

        # Group by video_id
        videos: dict[str, dict[str, Any]] = {}
        for meta in result["metadatas"]:
            if not meta or meta.get("source_type") != "youtube":
                continue

            vid = meta.get("video_id", "")
            if not vid:
                continue

            vid_subject = meta.get(META_MATIERE, "")
            if subject and vid_subject != subject:
                continue

            if vid not in videos:
                videos[vid] = {
                    "video_id": vid,
                    "url": meta.get(META_FILEPATH, f"https://youtube.com/watch?v={vid}"),
                    "subject": vid_subject,
                    "doc_type": meta.get(META_DOC_TYPE, "Video"),
                    "language": meta.get("language", ""),
                    "duration_seconds": meta.get("duration_seconds", 0),
                    "filename": meta.get(META_FILENAME, ""),
                    "chunks": 0,
                    "thumbnail": f"https://img.youtube.com/vi/{vid}/mqdefault.jpg",
                }
            videos[vid]["chunks"] += 1

        return sorted(videos.values(), key=lambda v: v["video_id"])

    def delete_indexed_video(self, video_id: str) -> dict[str, Any]:
        """Remove all chunks for a given video_id from ChromaDB."""
        from api.services.rag import rag_service

        store = rag_service.vectorstore
        result = store.get(include=["metadatas"])

        if not result or not result.get("ids"):
            return {"deleted": 0, "video_id": video_id}

        ids_to_delete = []
        for doc_id, meta in zip(result["ids"], result["metadatas"]):
            if meta and meta.get("source_type") == "youtube" and meta.get("video_id") == video_id:
                ids_to_delete.append(doc_id)

        if ids_to_delete:
            store.delete(ids=ids_to_delete)
            rag_service._bm25_index = None  # Invalidate BM25 cache

        return {"deleted": len(ids_to_delete), "video_id": video_id}

    def search_videos(
        self,
        concept: str,
        context: str = "",
        max_results: int = 5,
    ) -> dict[str, Any]:
        """
        Find relevant YouTube videos for a course concept.

        Generates search queries locally (no OpenAI call) and scrapes
        YouTube search results directly.  Fast and free.
        """
        # Build 2-3 simple search queries from the concept
        concept_clean = concept.strip().rstrip("?!. ")
        queries = [
            {"query": f"{concept_clean} explication cours", "description": "Recherche principale en français"},
            {"query": f"{concept_clean} tutorial", "description": "Recherche en anglais"},
        ]
        # If concept has multiple words, also try a shorter version
        if len(concept_clean.split()) >= 3:
            queries.append(
                {"query": concept_clean, "description": "Recherche directe"}
            )

        videos: list[dict[str, str]] = []
        seen_ids: set[str] = set()

        for q_item in queries:
            q = q_item["query"]
            try:
                fetched = self._scrape_youtube_search(q, max_results=max_results)
                for v in fetched:
                    vid = v.get("video_id", "")
                    if vid and vid not in seen_ids:
                        seen_ids.add(vid)
                        videos.append(v)
            except Exception as exc:
                logger.warning("YouTube scrape failed for '%s': %s", q, exc)

            if len(videos) >= max_results:
                break

        videos = videos[:max_results]

        return {
            "concept": concept,
            "queries": queries,
            "videos": videos,
            "recommended_channels": [],
            "tips": "",
            "total_found": len(videos),
        }

    @staticmethod
    def _scrape_youtube_search(
        query: str,
        max_results: int = 5,
    ) -> list[dict[str, str]]:
        """
        Scrape YouTube search results by parsing ytInitialData from the HTML.
        No API key required.
        """
        import re
        import json
        import urllib.parse
        import urllib.request

        encoded = urllib.parse.urlencode({"search_query": query})
        url = f"https://www.youtube.com/results?{encoded}"

        req = urllib.request.Request(url, headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Extract ytInitialData JSON from the page
        pattern = r"var\s+ytInitialData\s*=\s*(\{.+?\});"
        match = re.search(pattern, html)
        if not match:
            # Fallback pattern
            pattern2 = r"ytInitialData\"\s*:\s*(\{.+?\})\s*[,;]"
            match = re.search(pattern2, html)

        if not match:
            return []

        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return []

        # Navigate the nested JSON to find video renderers
        videos: list[dict[str, str]] = []

        try:
            contents = (
                data["contents"]["twoColumnSearchResultsRenderer"]
                ["primaryContents"]["sectionListRenderer"]["contents"]
            )
        except (KeyError, TypeError):
            return []

        for section in contents:
            items = (
                section.get("itemSectionRenderer", {})
                .get("contents", [])
            )
            for item in items:
                renderer = item.get("videoRenderer")
                if not renderer:
                    continue

                video_id = renderer.get("videoId", "")
                if not video_id:
                    continue

                title_runs = renderer.get("title", {}).get("runs", [])
                title = title_runs[0].get("text", "") if title_runs else ""

                channel_runs = (
                    renderer.get("ownerText", {}).get("runs", [])
                )
                channel = channel_runs[0].get("text", "") if channel_runs else ""

                length_text = (
                    renderer.get("lengthText", {})
                    .get("simpleText", "")
                )

                view_text = (
                    renderer.get("viewCountText", {})
                    .get("simpleText", "")
                )

                desc_runs = (
                    renderer.get("detailedMetadataSnippets", [{}])[0]
                    .get("snippetText", {}).get("runs", [])
                ) if renderer.get("detailedMetadataSnippets") else []
                description = " ".join(r.get("text", "") for r in desc_runs)

                thumbnail_url = ""
                thumbs = renderer.get("thumbnail", {}).get("thumbnails", [])
                if thumbs:
                    thumbnail_url = thumbs[-1].get("url", "")

                videos.append({
                    "video_id": video_id,
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "channel": channel,
                    "duration": length_text,
                    "views": view_text,
                    "description": description,
                    "thumbnail": thumbnail_url,
                })

                if len(videos) >= max_results:
                    return videos

        return videos


# Module-level singleton
youtube_service = YouTubeService()
