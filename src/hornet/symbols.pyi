# Copyright (c) 2025-2026 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from .terms import NonVariable as __BaseTerm__


def __getattr__(name: str) -> __BaseTerm__: ...
