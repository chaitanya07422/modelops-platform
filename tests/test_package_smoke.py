"""Smoke tests for the Milestone 0 package foundation.

These tests must stay free of network calls, credentials, and large datasets.
"""

from importlib.metadata import version

import modelops


def test_package_version_constant() -> None:
    assert modelops.__version__ == "0.1.0"


def test_installed_distribution_version() -> None:
    assert version("modelops") == "0.1.0"
