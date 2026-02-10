"""
Copilot Tools -- Complementary module using the GitHub Copilot SDK.

Provides structured visual tools (quiz, tables, charts, key concepts,
flashcards, mind maps) that run alongside the primary OpenAI-based RAG
pipeline.
"""

import json
import asyncio
import traceback
from typing import Any

# ---------------------------------------------------------------------------
# Conditional SDK import
# ---------------------------------------------------------------------------

try:
    from copilot import CopilotClient

    COPILOT_SDK_AVAILABLE = True
except ImportError:
    COPILOT_SDK_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_CONTENT_LENGTH: int = 6000
SESSION_TIMEOUT: float = 60.0
DEFAULT_MODEL: str = "gpt-4o"

AVAILABLE_MODELS: list[str] = [
    "gpt-4o",
    "gpt-4o-mini",
    "claude-sonnet-4",
    "o3-mini",
]

TOOL_LABELS: dict[str, str] = {
    "quiz": "Quiz",
    "table": "Tableau",
    "chart": "Graphique",
    "concepts": "Concepts",
    "flashcards": "Flashcards",
    "mindmap": "Mind Map",
}

_SYSTEM_MESSAGE: dict[str, str] = {
    "mode": "replace",
    "content": (
        "ROLE: Tu es un assistant JSON strict. Aucune exception.\n"
        "REGLES ABSOLUES:\n"
        "1. REPONSE UNIQUE: Un SEUL objet JSON {{ ... }}\n"
        "2. VALIDITE: Le JSON doit etre parsable par json.loads()\n"
        "3. FORMAT: Pas de markdown, pas de backticks, pas de texte avant/apres\n"
        "4. STRUCTURE: Commence par {{ et termine par }}\n"
        "5. VERIFICATION: Relis ta reponse - doit etre du JSON pur\n"
        "Genere UNIQUEMENT du JSON, rien d'autre."
    ),
}

_PROMPTS: dict[str, str] = {
    "quiz": (
        "Genere un quiz de {n} questions a choix multiples EN FRANCAIS.\n"
        "Format JSON STRICT :\n"
        '{{"title":"Quiz : ...","questions":[{{"question":"...","options":'
        '["A) ...","B) ...","C) ...","D) ..."],"correct":0,"explanation":"..."}}]}}\n\n'
        "Contenu :\n{content}"
    ),
    "table": (
        "Genere un tableau recapitulatif EN FRANCAIS.\n"
        "Format JSON STRICT :\n"
        '{{"title":"...","headers":["Col1","Col2"],"rows":[["val1","val2"]]}}\n\n'
        "Contenu :\n{content}"
    ),
    "chart": (
        "Genere des donnees pour un graphique EN FRANCAIS.\n"
        "Si pas de donnees numeriques, invente des valeurs pertinentes "
        "(importance, frequence, complexite, %).\n"
        'Format JSON STRICT : {{"title":"...","chart_type":"bar",'
        '"labels":["l1","l2"],"values":[10,20]}}\n\n'
        "Contenu :\n{content}"
    ),
    "concepts": (
        "Extrais les concepts cles EN FRANCAIS avec definitions concises.\n"
        'Format JSON STRICT : {{"title":"Concepts cles","concepts":'
        '[{{"name":"...","definition":"...","importance":"haute|moyenne|basse"}}]}}\n\n'
        "Contenu :\n{content}"
    ),
    "flashcards": (
        "Genere des flashcards de revision EN FRANCAIS.\n"
        'Format JSON STRICT : {{"title":"Flashcards","cards":'
        '[{{"front":"Question","back":"Reponse"}}]}}\n\n'
        "Contenu :\n{content}"
    ),
    "mindmap": (
        "Genere une carte mentale structuree EN FRANCAIS.\n"
        'Format JSON STRICT : {{"title":"...","central":"Concept central",'
        '"branches":[{{"name":"...","children":["..."]}}]}}\n\n'
        "Contenu :\n{content}"
    ),
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_json_object(text: str) -> str:
    """Extract the outermost JSON object ``{...}`` from *text*."""
    cleaned = text.strip()

    if cleaned.startswith("```"):
        end_fence = cleaned.find("```", 3)
        if end_fence != -1:
            cleaned = cleaned[3:end_fence].strip()
        else:
            cleaned = cleaned[3:].strip()

    cleaned = cleaned.strip("`").strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        return cleaned[start : end + 1]

    return cleaned


def _format_sources_block(sources: list[dict[str, str]]) -> str:
    """Build a plain-text sources block to append to the prompt."""
    lines: list[str] = ["\n\nSources utilisees :"]
    for src in sources:
        if isinstance(src, dict):
            matiere = src.get("matiere", "Inconnu")
            doc_type = src.get("doc_type", "Doc")
            filename = src.get("filename", "")
            lines.append(f"- {matiere} ({doc_type}): {filename}")
        else:
            lines.append(f"- {src}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Async generation
# ---------------------------------------------------------------------------


async def _generate_async(
    tool_type: str,
    content: str,
    model: str = DEFAULT_MODEL,
    n: int = 5,
    sources: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Generate structured JSON content through the Copilot SDK."""
    template = _PROMPTS.get(tool_type)
    if template is None:
        return {"error": f"Type d'outil inconnu : {tool_type}"}

    prompt_text = template.format(
        content=content[:MAX_CONTENT_LENGTH],
        n=n,
    )
    if sources:
        prompt_text += _format_sources_block(sources)

    client = CopilotClient()
    try:
        await client.start()

        session = await client.create_session(
            {
                "model": model,
                "system_message": _SYSTEM_MESSAGE,
                "streaming": False,
            }
        )

        try:
            event = await session.send_and_wait(
                {"prompt": prompt_text},
                timeout=SESSION_TIMEOUT,
            )

            raw = ""
            if event and hasattr(event, "data") and event.data:
                raw = getattr(event.data, "content", "") or ""

            if not raw:
                return {"error": "Aucune reponse du modele Copilot."}

            original_raw = raw
            json_str = _extract_json_object(raw)

            try:
                result = json.loads(json_str)
            except json.JSONDecodeError as exc:
                return {
                    "error": "JSON invalide",
                    "raw": original_raw[:500],
                    "exception": str(exc),
                }

            if not isinstance(result, dict):
                return {
                    "error": "La reponse JSON n'est pas un objet",
                    "raw": original_raw[:500],
                    "exception": f"Type obtenu : {type(result).__name__}",
                }

            if sources:
                result["sources"] = sources

            return result

        finally:
            try:
                await session.destroy()
            except Exception:
                pass

    except Exception as exc:
        return {"error": f"Erreur Copilot : {exc}"}
    finally:
        try:
            await client.stop()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def is_copilot_ready() -> bool:
    """Return ``True`` when the Copilot SDK is importable."""
    return COPILOT_SDK_AVAILABLE


def get_available_models() -> list[str]:
    """Return the list of known Copilot-compatible model identifiers."""
    if not COPILOT_SDK_AVAILABLE:
        return []
    return list(AVAILABLE_MODELS)


def copilot_generate(
    tool_type: str,
    content: str,
    model: str = DEFAULT_MODEL,
    n: int = 5,
    sources: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Synchronous entry point for Copilot content generation."""
    if not COPILOT_SDK_AVAILABLE:
        return {"error": "SDK Copilot non installe."}

    try:
        return asyncio.run(
            _generate_async(tool_type, content, model, n, sources)
        )
    except Exception as exc:
        return {
            "error": f"Erreur lors de la generation : {exc}",
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc()[:500],
        }
