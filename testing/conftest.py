import pytest
import sys
import os

pytest_plugins = [
    "fixtures.main",
]


sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
)
