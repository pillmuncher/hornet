from .expressions import Expression as __Expression__

__all__ = []


def __getattr__(name: str) -> __Expression__: ...
