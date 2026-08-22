"""Portable AI distribution runtime for Metaphysics Lab.

The public entry point is :func:`dispatch`.  Importing this package must stay
lightweight so ``runtime_info`` can work even when optional calculation
packages are unavailable.
"""

from .runtime import dispatch

__all__ = ["dispatch"]
