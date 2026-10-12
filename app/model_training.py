"""
CreditLens - Forwarder for model_training module.
Guarantees resolving 'from model_training import ...' when working directory or script is app/.
"""
import os
import sys

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_BASE, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

if "src.model_training" in sys.modules and getattr(sys.modules["src.model_training"], "__file__", None):
    _mod = sys.modules["src.model_training"]
else:
    import importlib.util
    _spec = importlib.util.spec_from_file_location("model_training", os.path.join(_SRC, "model_training.py"))
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules["model_training"] = _mod
    sys.modules["src.model_training"] = _mod
    _spec.loader.exec_module(_mod)

for _k, _v in _mod.__dict__.items():
    if not _k.startswith("__"):
        globals()[_k] = _v
