#!/usr/bin/env python3
"""Deprecated URAS compatibility entry point for LoopSpec 2.x."""

import sys

try:
    from .loopspec import main
except ImportError:  # direct `python3 tools/uras.py`
    from loopspec import main


def legacy_main(argv=None):
    print(
        "warning: `uras` was renamed to `loopspec`; the compatibility command "
        "will be removed in LoopSpec 3.0",
        file=sys.stderr,
    )
    return main(argv)


if __name__ == "__main__":
    sys.exit(legacy_main())
