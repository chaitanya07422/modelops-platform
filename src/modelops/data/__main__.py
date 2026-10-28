"""CLI: ``python -m modelops.data`` downloads one TLC yellow taxi month."""

from __future__ import annotations

import argparse
import logging
import sys

from modelops.config import load_config
from modelops.data.download import download_yellow_taxi_month


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download one TLC yellow taxi Parquet month")
    parser.add_argument("--force", action="store_true", help="Re-download even if file exists")
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout seconds")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = load_config()
    try:
        result = download_yellow_taxi_month(config, force=args.force, timeout_seconds=args.timeout)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        logging.error("%s", exc)
        return 1

    print(f"path={result.path}")
    print(f"url={result.url}")
    print(f"downloaded={result.downloaded}")
    print(f"bytes={result.bytes_written}")
    print(f"download_date_utc={result.download_date_utc}")
    print(f"message={result.message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
