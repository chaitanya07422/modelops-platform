#!/usr/bin/env python3
"""Thin wrapper: prefer ``python -m modelops.data`` from an editable install."""

from __future__ import annotations

import runpy
import sys


def main() -> int:
    sys.argv = [sys.argv[0], *sys.argv[1:]]
    runpy.run_module("modelops.data", run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
