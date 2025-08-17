from functools import lru_cache

from hornet.expressions import Name

__all__ = []
__getattr__ = lru_cache(Name)
