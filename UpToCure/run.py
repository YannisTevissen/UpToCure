#!/usr/bin/env python
"""UpToCure application entry point.

Usage:
    python run.py            # development server on $PORT (default 8000)
    FLASK_DEBUG=1 python run.py
"""

from __future__ import annotations

import os

from src.app import app


def main() -> None:
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
