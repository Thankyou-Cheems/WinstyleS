"""
通用工具模块
"""

from winstyles.utils.hashing import compute_hash, verify_hash
from winstyles.utils.path import collapse_vars, expand_vars, normalize_path

__all__ = [
    "expand_vars",
    "collapse_vars",
    "normalize_path",
    "compute_hash",
    "verify_hash",
]
