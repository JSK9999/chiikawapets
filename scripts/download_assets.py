#!/usr/bin/env python3
"""CLI wrapper: python scripts/download_assets.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from chiikawapets.download import main  # noqa: E402

raise SystemExit(main())
