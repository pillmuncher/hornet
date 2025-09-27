from __future__ import annotations

from .terms import BaseTerm as __BaseTerm__


def __getattr__(name: str) -> __BaseTerm__: ...
