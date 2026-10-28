"""Download a single TLC yellow taxi monthly Parquet file.

Downloads are optional for CI: tests use synthetic fixtures under
``data/fixtures/``. Training scripts call this when a local raw file is missing.
"""

from __future__ import annotations

import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from modelops.config import AppConfig, load_config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DownloadResult:
    """Metadata recorded after a successful or skipped download attempt."""

    path: Path
    url: str
    downloaded: bool
    download_date_utc: str | None
    bytes_written: int | None
    message: str


def download_yellow_taxi_month(
    config: AppConfig | None = None,
    *,
    force: bool = False,
    timeout_seconds: float = 120.0,
) -> DownloadResult:
    """Fetch one month of yellow taxi trips into ``config.raw_dir``.

    Parameters
    ----------
    config:
        Resolved app config. Loaded from defaults when omitted.
    force:
        Re-download even if the destination file already exists.
    timeout_seconds:
        Network timeout for the HTTP GET.

    Returns
    -------
    DownloadResult
        Path and provenance fields. Raises ``FileNotFoundError`` / network
        errors only when a download is required and fails — callers should not
        invent trip rows as a fallback.
    """
    cfg = config or load_config()
    destination = cfg.raw_parquet_path
    url = cfg.resolved_data_url
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and not force:
        size = destination.stat().st_size
        logger.info("Using existing raw file %s (%s bytes)", destination, size)
        return DownloadResult(
            path=destination,
            url=url,
            downloaded=False,
            download_date_utc=None,
            bytes_written=size,
            message="existing_file",
        )

    logger.info("Downloading %s -> %s", url, destination)
    tmp_path = destination.with_suffix(".parquet.partial")

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "modelops/0.1 (portfolio learning)"},
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            data = response.read()
        tmp_path.write_bytes(data)
        tmp_path.replace(destination)
    except urllib.error.URLError as exc:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Failed to download TLC data from {url}. "
            "Network may be unavailable; place the Parquet file manually at "
            f"{destination} or use data/fixtures for tests. Original error: {exc}"
        ) from exc
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise

    download_date = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    size = destination.stat().st_size
    logger.info("Wrote %s bytes on %s", size, download_date)
    return DownloadResult(
        path=destination,
        url=url,
        downloaded=True,
        download_date_utc=download_date,
        bytes_written=size,
        message="downloaded",
    )
