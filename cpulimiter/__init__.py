"""
cpulimiter - A simple, lightweight Python library for Windows to limit CPU usage of processes.
"""

__version__ = "1.0.2"
__author__ = "Ahmed Ashraf"

from .limiter import CpuLimiter
from .utils import get_active_window_info, get_active_app_pids

__all__ = ["CpuLimiter", "get_active_window_info", "get_active_app_pids"]
