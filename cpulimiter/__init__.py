"""
CPU Limiter
A Python library to limit the CPU usage of processes.
"""

__version__ = "1.0.0"

from .limiter import CpuLimiter
from .utils import get_active_app_pids
