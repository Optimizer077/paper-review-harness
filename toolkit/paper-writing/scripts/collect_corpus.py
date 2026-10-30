#!/usr/bin/env python3
"""Compatibility entrypoint for the active 300-paper, <=2022 collector.

Run with --output-root DIRECTORY [--collect]. The earlier broad corpus collector
is retained under research/archive/initial-build, outside the active skill.
"""
from collect_historical import main
if __name__ == "__main__":
    raise SystemExit(main())
