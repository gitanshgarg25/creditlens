from __future__ import annotations
import os
import sys
import importlib.util

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_BASE, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

_fpath = os.path.join(_SRC, "model_training.py")
if os.path.exists(_fpath):
    _spec = importlib.util.spec_from_file_location("src.model_training", _fpath)
    if _spec and _spec.loader:
        _mod = importlib.util.module_from_spec(_spec)
        sys.modules["model_training"] = _mod
        sys.modules["src.model_training"] = _mod
        _spec.loader.exec_module(_mod)
        for _k, _v in _mod.__dict__.items():
            if not _k.startswith("__"):
                globals()[_k] = _v
