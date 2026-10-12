"""
CreditLens - Forwarder for risk_scoring module.
Guarantees resolving 'from risk_scoring import ...' when working directory or script is app/.
"""
import os
import sys

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_BASE, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

if "src.risk_scoring" in sys.modules and getattr(sys.modules["src.risk_scoring"], "__file__", None):
    _mod = sys.modules["src.risk_scoring"]
else:
    import importlib.util
    _spec = importlib.util.spec_from_file_location("risk_scoring", os.path.join(_SRC, "risk_scoring.py"))
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules["risk_scoring"] = _mod
    sys.modules["src.risk_scoring"] = _mod
    _spec.loader.exec_module(_mod)

for _k, _v in _mod.__dict__.items():
    if not _k.startswith("__"):
        globals()[_k] = _v
