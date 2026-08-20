#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Metaphysics Lab 八字引擎相容入口。

正式實作位於 ``engine.bazi.calendar``。本檔保留既有 import 與 CLI 路徑。
"""
from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.bazi.calendar import *  # noqa: F401,F403
from engine.bazi.calendar import main

if __name__ == "__main__":
    main()
