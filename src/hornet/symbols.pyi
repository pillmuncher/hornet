from __future__ import annotations

from .terms import NonVariable as __BaseTerm__


def __getattr__(name: str) -> __BaseTerm__: ...
