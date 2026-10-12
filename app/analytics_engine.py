"""
CreditLens - Forwarder for analytics_engine module.
Guarantees resolving 'from analytics_engine import ...' when working directory or script is app/.
"""
import os
import sys

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_BASE, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

if "src.analytics_engine" in sys.modules and getattr(sys.modules["src.analytics_engine"], "__file__", None):
    _mod = sys.modules["src.analytics_engine"]
else:
    import importlib.util
    _spec = importlib.util.spec_from_file_location("analytics_engine", os.path.join(_SRC, "analytics_engine.py"))
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules["analytics_engine"] = _mod
    sys.modules["src.analytics_engine"] = _mod
    _spec.loader.exec_module(_mod)

for _k, _v in _mod.__dict__.items():
    if not _k.startswith("__"):
        globals()[_k] = _v
