"""Fixture to block all real network calls during tests."""

import socket
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Block all real network calls during tests (fail if attempted)."""

    def guard(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("Network calls are blocked during tests!")

    monkeypatch.setattr(socket, "socket", guard)
