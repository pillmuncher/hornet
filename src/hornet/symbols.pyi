from __future__ import annotations

from .expressions import Expression as __Expression__


def __getattr__(name: str) -> __Expression__: ...
