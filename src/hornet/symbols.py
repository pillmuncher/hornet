# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

# symbols.__getattr__ returns Atom | Variable | Wildcard based on naming
# convention (lowercase -> Atom, uppercase -> Variable, _ -> Wildcard).
# Python's type system cannot encode this dependency on string content
# (it would require dependent types), so call sites that use the result
# as NonVariable carry an unavoidable type imprecision.
# Runtime behavior is correct; pyright is appeased by the broader union.

from .terms import symbol as __getattr__

__all__ = ()
