import os
import sys

# 让 `python -m evaluation.compare` 和 `python evaluation/compare.py` 都能 import 到项目根
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
