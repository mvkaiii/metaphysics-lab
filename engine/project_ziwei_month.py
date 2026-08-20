#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Metaphysics Lab 紫微流月引擎相容入口。

正式實作位於 ``engine.ziwei.month``。本檔保留既有 import 與 CLI 路徑。
"""
from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.ziwei.month import *  # noqa: F401,F403
from engine.ziwei.month import main

if __name__ == "__main__":
    main()
