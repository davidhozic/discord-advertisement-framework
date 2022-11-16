import pytest
import sys
import os

pytest_plugins = [
    "fixtures.main",
]


sys.path.append(
    os.path.abspath("../src/")
)