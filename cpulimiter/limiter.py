import ctypes
import ctypes.wintypes
import threading
import time
import psutil
import pygetwindow as gw
import win32process
import os

# Windows API constants
THREAD_SUSPEND_RESUME = 0x0002
THREAD_QUERY_INFORMATION = 0x0040

# Windows API functions
kernel32 = ctypes.windll.kernel32
OpenThread = kernel32.OpenThread
OpenThread.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD]
OpenThread.restype = ctypes.wintypes.HANDLE

SuspendThread = kernel32.SuspendThread
SuspendThread.argtypes = [ctypes.wintypes.HANDLE]
SuspendThread.restype = ctypes.wintypes.DWORD

ResumeThread = kernel32.ResumeThread
ResumeThread.argtypes = [ctypes.wintypes.HANDLE]
ResumeThread.restype = ctypes.wintypes.DWORD

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
CloseHandle.restype = ctypes.wintypes.BOOL

class _ProcessLimiter:
    """Internal class to limit a single process. This contains the original core logic."""
    def __init__(self, pid, limit_percentage):
        self.pid = pid
        self.limit_percentage = limit_percentage
        self.active = False
        self.thread = None
        self.stop_event = threading.Event()
        self._thread_handles = {}
        self._last_thread_update = 0

    def start(self):
        if not self.active:
            self.active = True
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._limit_loop)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        if self.active:
            self.active = False
            self.stop_event.set()
            self._resume_all_threads()
            if self.thread:
                self.thread.join(timeout=2)

    def _get_thread_ids(self):
        try:
            process = psutil.Process(self.pid)
            return [thread.id for thread in process.threads()]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []

    def _get_or_create_handle(self, tid):
        if tid not in self._thread_handles:
            handle = OpenThread(THREAD_SUSPEND_RESUME, False, tid)
            if handle:
                self._thread_handles[tid] = handle
        return self._thread_handles.get(tid)

    def _cleanup_handles(self):
        for handle in self._thread_handles.values():
            CloseHandle(handle)
        self._thread_handles.clear()

    def _suspend_all_threads(self):
        for tid in self._get_thread_ids():
            handle = self._get_or_create_handle(tid)
            if handle:
                SuspendThread(handle)

    def _resume_all_threads(self):
        for tid in self._get_thread_ids():
            handle = self._get_or_create_handle(tid)
            if handle:
                ResumeThread(handle)

    def _limit_loop(self):
        cycle_time = 5.0
        suspend_time = cycle_time * (self.limit_percentage / 100.0)
        resume_time = cycle_time - suspend_time

        while self.active and not self.stop_event.is_set():
            try:
                current_time = time.time()
                if current_time - self._last_thread_update > 30:
                    self._cleanup_handles()
                    self._last_thread_update = current_time
                
                self._suspend_all_threads()
                self.stop_event.wait(suspend_time)

                if not self.active:
                    break
                    
                self._resume_all_threads()
                self.stop_event.wait(resume_time)
                
            except Exception:
                break
        
        self._resume_all_threads()
        self._cleanup_handles()

class CpuLimiter:
    """Manages and applies CPU limits to one or more processes."""
    def __init__(self, processes_to_limit: dict = None):
        """
        Initializes the CpuLimiter.

        Args:
            processes_to_limit (dict, optional): A dictionary where keys are process identifiers
                                                 (name, pid, or window title part) and values are
                                                 the limit percentage. If provided, automatically
                                                 adds and starts limiting these processes.
                                                 Example: {"chrome.exe": 95, 1234: 90}
        """
        self._limiters = {}  # Stores {pid: _ProcessLimiter object}
        self._process_info = {} # Stores {pid: info dict}

        if processes_to_limit:
            for identifier, limit in processes_to_limit.items():
                # Determine the type of identifier and call add() accordingly
                if isinstance(identifier, int): # PID
                    self.add(pid=identifier, limit_percentage=limit)
                elif isinstance(identifier, str) and (identifier.endswith(".exe") or "." in identifier): # Process Name
                    self.add(process_name=identifier, limit_percentage=limit)
                elif isinstance(identifier, str): # Window Title
                    self.add(window_title_contains=identifier, limit_percentage=limit)
            self.start_all()

    def _find_pids_by_name(self, process_name):
        pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == process_name:
                pids.append(proc.info['pid'])
        return pids

    def _find_pids_by_window_title(self, title_substring):
        pids = []
        for window in gw.getAllWindows():
            if window.visible and title_substring in window.title:
                try:
                    _, pid = win32process.GetWindowThreadProcessId(window._hWnd)
                    if pid not in pids:
                        pids.append(pid)
                except Exception:
                    continue
        return pids

    def add(self, pid=None, process_name=None, window_title_contains=None, limit_percentage=98):
        """Adds a process to be limited."""
        if not any([pid, process_name, window_title_contains]):
            raise ValueError("Must provide a pid, process_name, or window_title_contains.")

        target_pids = []
        if pid:
            target_pids.append(pid)
        if process_name:
            target_pids.extend(self._find_pids_by_name(process_name))
        if window_title_contains:
            target_pids.extend(self._find_pids_by_window_title(window_title_contains))
        
        for p in set(target_pids):
            if p not in self._limiters:
                self._process_info[p] = {
                    "pid": p,
                    "process_name": process_name,
                    "window_title_contains": window_title_contains,
                    "limit_percentage": limit_percentage
                }
                self._limiters[p] = _ProcessLimiter(p, limit_percentage)

    def remove(self, pid=None, process_name=None, window_title_contains=None):
        """Removes a process from the limiter."""
        pids_to_remove = self._get_pids_for_criteria(pid, process_name, window_title_contains)
        for p in pids_to_remove:
            if p in self._limiters:
                self._limiters[p].stop()
                del self._limiters[p]
                del self._process_info[p]

    def start(self, pid=None, process_name=None, window_title_contains=None):
        """Starts limiting a specific process/group that has been added."""
        pids_to_start = self._get_pids_for_criteria(pid, process_name, window_title_contains)
        for p in pids_to_start:
            if p in self._limiters:
                self._limiters[p].start()

    def stop(self, pid=None, process_name=None, window_title_contains=None):
        """Stops limiting a specific process/group."""
        pids_to_stop = self._get_pids_for_criteria(pid, process_name, window_title_contains)
        for p in pids_to_stop:
            if p in self._limiters:
                self._limiters[p].stop()

    def start_all(self):
        """Starts limiting all added processes."""
        for limiter in self._limiters.values():
            limiter.start()

    def stop_all(self):
        """Stops limiting all added processes."""
        for limiter in self._limiters.values():
            limiter.stop()

    def shutdown(self):
        """A convenient alias for stop_all()."""
        self.stop_all()

    def get_active(self):
        """Returns a list of actively limited processes."""
        return [info for pid, info in self._process_info.items() if self._limiters[pid].active]

    def _get_pids_for_criteria(self, pid=None, process_name=None, window_title_contains=None):
        """Helper to find PIDs matching the given criteria from the managed list."""
        if pid:
            return [pid]
        
        found_pids = []
        for p, info in self._process_info.items():
            if process_name and info["process_name"] == process_name:
                found_pids.append(p)
            if window_title_contains and info["window_title_contains"] == window_title_contains:
                found_pids.append(p)
        return found_pids

