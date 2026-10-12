from __future__ import annotations
import os
import sys

# Setup Project Paths & Namespace Cleanse
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")
APP_DIR = os.path.join(ROOT_DIR, "app")

sys.path = [p for p in sys.path if os.path.abspath(p) not in ("/mount/src", "/mount")]
for _p in [SRC_DIR, ROOT_DIR, APP_DIR]:
    while _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

# Import and execute main Streamlit application
from app.streamlit_app import main

if __name__ == "__main__":
    main()
else:
    main()
