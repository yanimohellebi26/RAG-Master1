#!/usr/bin/env python3
"""
CLI wrapper for evaluation.

Usage:
    python -m scripts.evaluate
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluation.evaluator import main

if __name__ == "__main__":
    main()
