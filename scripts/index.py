#!/usr/bin/env python3
"""
CLI wrapper for indexation.

Usage:
    python -m scripts.index              # full indexation
    python -m scripts.index -i           # incremental
    python -m scripts.index -f           # force full rebuild
    python -m scripts.index -w           # watch mode
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.indexer import main as run_indexer
from core.watcher import watch_and_reindex


def cli() -> None:
    parser = argparse.ArgumentParser(description="Indexation RAG Master 1")
    parser.add_argument("--incremental", "-i", action="store_true",
                        help="Reindexer uniquement les fichiers modifies")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Forcer une reindexation complete")
    parser.add_argument("--watch", "-w", action="store_true",
                        help="Activer le mode surveillance")
    args = parser.parse_args()

    if args.watch:
        watch_and_reindex()
    else:
        run_indexer(incremental=args.incremental, force_full=args.force)


if __name__ == "__main__":
    cli()
