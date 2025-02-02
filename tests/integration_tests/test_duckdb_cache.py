# Copyright (c) 2023 Airbyte, Inc., all rights reserved.

"""Integration tests which leverage the source-faker connector to test the framework end-to-end.

Since source-faker is included in dev dependencies, we can assume `source-faker` is installed
and available on PATH for the poetry-managed venv.
"""
from __future__ import annotations

from collections.abc import Generator
import os
import sys
import shutil

import pytest
import ulid


import airbyte as ab
from airbyte.caches.duckdb import DuckDBCache
from airbyte.caches.util import new_local_cache, get_default_cache

# Product count is always the same, regardless of faker scale.
NUM_PRODUCTS = 100

SEED_A = 1234
SEED_B = 5678

# Number of records in each of the 'users' and 'purchases' streams.
FAKER_SCALE_A = 200
# We want this to be different from FAKER_SCALE_A.
FAKER_SCALE_B = 300


# Patch PATH to include the source-faker executable.

@pytest.fixture(autouse=True)
def add_venv_bin_to_path(monkeypatch):
    # Get the path to the bin directory of the virtual environment
    venv_bin_path = os.path.join(sys.prefix, 'bin')

    # Add the bin directory to the PATH
    new_path = f"{venv_bin_path}:{os.environ['PATH']}"
    monkeypatch.setenv('PATH', new_path)


@pytest.fixture(scope="function")  # Each test gets a fresh source-faker instance.
def source_faker() -> ab.Source:
    """Fixture to return a source-faker connector instance."""
    source = ab.get_source(
        "source-faker",
        local_executable="source-faker",
        config={
            "count": FAKER_SCALE_A,
            "seed": SEED_A,
            "parallelism": 16,  # Otherwise defaults to 4.
        },
        install_if_missing=False,  # Should already be on PATH
    )
    source.check()
    source.select_streams([
        "users",
        "products",
        "purchases",
    ])
    return source



@pytest.fixture(scope="function")
def duckdb_cache() -> Generator[DuckDBCache, None, None]:
    """Fixture to return a fresh cache."""
    cache: DuckDBCache = new_local_cache()
    yield cache
    # TODO: Delete cache DB file after test is complete.
    return


def test_which_source_faker() -> None:
    """Test that source-faker is available on PATH."""
    assert shutil.which("source-faker") is not None, \
        f"Can't find source-faker on PATH: {os.environ['PATH']}"


def test_duckdb_cache(duckdb_cache: DuckDBCache) -> None:
    """Test that the duckdb cache is available."""
    assert duckdb_cache
    assert isinstance(duckdb_cache, DuckDBCache)
