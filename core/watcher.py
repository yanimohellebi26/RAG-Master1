"""
Watch mode -- Monitors the courses directory and triggers incremental
reindexing when file modifications are detected.
"""

import os
import time
import signal
import sys
import fnmatch
from pathlib import Path
from datetime import datetime

from core.config import CONFIG, COURSES_DIR, SUPPORTED_EXTENSIONS, EXCLUDED_PATTERNS


def get_directory_hash(directory: Path) -> dict[str, tuple[float, int]]:
    """Get a snapshot of all files with their modification time and size.

    Returns a dict mapping filepath -> (mtime, size).
    """
    file_states: dict[str, tuple[float, int]] = {}

    for root, _, files in os.walk(directory):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            filepath = os.path.join(root, filename)

            rel_path = os.path.relpath(filepath, directory)
            skip = False
            for pattern in EXCLUDED_PATTERNS:
                if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(filename, pattern):
                    skip = True
                    break

            if skip:
                continue

            try:
                stat = os.stat(filepath)
                file_states[filepath] = (stat.st_mtime, stat.st_size)
            except OSError:
                pass

    return file_states


def watch_and_reindex() -> None:
    """Watch the courses directory and reindex when changes are detected."""
    from core.indexer import main as run_indexer

    watch_config = CONFIG.get("watch_mode", {})

    if not watch_config.get("enabled", False):
        print("Mode watch desactive dans config.yaml")
        print("Activez-le avec: watch_mode.enabled = true")
        return

    check_interval = watch_config.get("check_interval_seconds", 60)
    auto_reindex = watch_config.get("auto_reindex", True)

    print("=" * 60)
    print("Mode surveillance actif - RAG Master 1")
    print("=" * 60)
    print(f"Dossier surveille : {COURSES_DIR}")
    print(f"Intervalle de verification : {check_interval}s")
    print(f"Auto-reindexation : {'Oui' if auto_reindex else 'Non'}")
    print("\nCtrl+C pour arreter\n")

    print("Snapshot initial...")
    previous_state = get_directory_hash(COURSES_DIR)
    print(f"  {len(previous_state)} fichiers surveilles\n")

    def signal_handler(sig, frame):
        print("\n\nArret de la surveillance...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    check_count = 0
    while True:
        time.sleep(check_interval)
        check_count += 1

        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"[{current_time}] Verification #{check_count}...", end=" ")

        current_state = get_directory_hash(COURSES_DIR)

        added = set(current_state.keys()) - set(previous_state.keys())
        removed = set(previous_state.keys()) - set(current_state.keys())
        modified = {
            fp for fp in current_state
            if fp in previous_state and current_state[fp] != previous_state[fp]
        }

        if added or removed or modified:
            print("CHANGEMENTS DETECTES")

            if added:
                print(f"  + {len(added)} fichiers ajoutes:")
                for fp in sorted(added)[:5]:
                    print(f"    - {os.path.basename(fp)}")
                if len(added) > 5:
                    print(f"    ... et {len(added) - 5} autres")

            if removed:
                print(f"  - {len(removed)} fichiers supprimes:")
                for fp in sorted(removed)[:5]:
                    print(f"    - {os.path.basename(fp)}")
                if len(removed) > 5:
                    print(f"    ... et {len(removed) - 5} autres")

            if modified:
                print(f"  ~ {len(modified)} fichiers modifies:")
                for fp in sorted(modified)[:5]:
                    print(f"    - {os.path.basename(fp)}")
                if len(modified) > 5:
                    print(f"    ... et {len(modified) - 5} autres")

            if auto_reindex:
                print("\nLancement de la reindexation incrementale...")
                print("-" * 60)
                try:
                    run_indexer(incremental=True, force_full=False)
                    print("-" * 60)
                    print("Reindexation terminee.\n")
                except Exception as exc:
                    print(f"ERREUR lors de la reindexation: {exc}\n")
            else:
                print("\nAuto-reindexation desactivee. Lancez manuellement:")
                print("  python -m scripts.index --incremental\n")

            previous_state = current_state
        else:
            print("Aucun changement")


if __name__ == "__main__":
    watch_and_reindex()
