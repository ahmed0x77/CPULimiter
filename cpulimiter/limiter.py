import ctypes
import ctypes.wintypes
import atexit
import psutil
import pygetwindow as gw
import win32process
import os
import time

# --- C++ Engine Loader (Singleton) ---
class _Engine:
    def __init__(self):
        self.dll = None
        try:
            dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'limiter_engine.dll')
            if not os.path.exists(dll_path):
                raise FileNotFoundError(f"limiter_engine.dll not found in the package directory.")

            self.dll = ctypes.CDLL(dll_path)
            self._configure_functions()
            self.dll.StartLimiter()
            atexit.register(self.shutdown)
            print("✅ CPU Limiter Engine (C++) Loaded and Started.")

        except (FileNotFoundError, OSError) as e:
            print("❌ CRITICAL ERROR: Could not load limiter_engine.dll.")
            raise RuntimeError(f"Engine loading failed: {e}. Ensure the 64-bit DLL is in the correct folder.")

    def _configure_functions(self):
        self.dll.StartLimiter.restype = None
        self.dll.StopLimiter.restype = None
        self.dll.AddProcess.argtypes = [ctypes.wintypes.DWORD, ctypes.c_int]
        self.dll.AddProcess.restype = None
        self.dll.RemoveProcess.argtypes = [ctypes.wintypes.DWORD]
        self.dll.RemoveProcess.restype = None
        self.dll.GetManagedPids.argtypes = [ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.c_int]
        self.dll.GetManagedPids.restype = ctypes.c_int

    def add_process(self, pid, limit):
        if self.dll: self.dll.AddProcess(pid, limit)
    def remove_process(self, pid):
        if self.dll: self.dll.RemoveProcess(pid)
    def shutdown(self):
        if self.dll:
            print("Shutting down C++ Limiter Engine...")
            self.dll.StopLimiter()
            self.dll = None

engine = _Engine()

class CpuLimiter:
    """
    Manages and applies CPU limits to one or more processes.
    This class maintains 100% backward compatibility with the original pure-Python API,
    while using a high-performance C++ backend for its core logic.
    """
    def __init__(self, processes_to_limit: dict = None):
        # --- FIX: REMOVED THE UNNECESSARY CALL TO `engine.is_loaded()` ---
        # The program will have already crashed if the engine failed to load,
        # so this check was redundant and caused the error.
        
        self._process_info = {}
        self._active_pids = set()

        if processes_to_limit:
            for identifier, limit in processes_to_limit.items():
                if isinstance(identifier, int): self.add(pid=identifier, limit_percentage=limit)
                elif isinstance(identifier, str) and (identifier.endswith(".exe") or "." in identifier): self.add(process_name=identifier, limit_percentage=limit)
                elif isinstance(identifier, str): self.add(window_title_contains=identifier, limit_percentage=limit)
            self.start_all()

    def _find_pids_by_name(self, process_name):
        return [p.pid for p in psutil.process_iter(['pid', 'name']) if p.info['name'].lower() == process_name.lower()]
    def _find_pids_by_window_title(self, title_substring):
        pids = set()
        for window in gw.getAllWindows():
            if window.visible and title_substring.lower() in window.title.lower():
                try: _, pid = win32process.GetWindowThreadProcessId(window._hWnd)
                except Exception: continue
                pids.add(pid)
        return list(pids)

    def add(self, pid=None, process_name=None, window_title_contains=None, limit_percentage=98):
        """Adds a process to be managed. Does NOT start limiting it yet."""
        if not any([pid, process_name, window_title_contains]): raise ValueError("Must provide an identifier.")
        target_pids = []
        if pid: target_pids.append(pid)
        if process_name: target_pids.extend(self._find_pids_by_name(process_name))
        if window_title_contains: target_pids.extend(self._find_pids_by_window_title(window_title_contains))
        for p in set(target_pids):
            if p not in self._process_info:
                self._process_info[p] = { "pid": p, "process_name": process_name, "window_title_contains": window_title_contains, "limit_percentage": limit_percentage }

    def remove(self, pid=None, process_name=None, window_title_contains=None):
        """Stops limiting and completely removes a process from management."""
        pids_to_remove = self._get_pids_for_criteria(pid, process_name, window_title_contains)
        for p in pids_to_remove:
            if p in self._process_info:
                if p in self._active_pids:
                    engine.remove_process(p)
                    self._active_pids.remove(p)
                del self._process_info[p]

    def start(self, pid=None, process_name=None, window_title_contains=None):
        """Starts limiting a specific process/group that has been added."""
        pids_to_start = self._get_pids_for_criteria(pid, process_name, window_title_contains)
        for p in pids_to_start:
            if p in self._process_info and p not in self._active_pids:
                limit = self._process_info[p]['limit_percentage']
                engine.add_process(p, limit)
                self._active_pids.add(p)

    def stop(self, pid=None, process_name=None, window_title_contains=None):
        """Stops limiting a specific process/group but keeps it in the added list."""
        pids_to_stop = self._get_pids_for_criteria(pid, process_name, window_title_contains)
        for p in pids_to_stop:
            if p in self._active_pids:
                engine.remove_process(p)
                self._active_pids.remove(p)

    def start_all(self):
        """Starts limiting all processes that have been added."""
        for p in list(self._process_info.keys()): self.start(pid=p)

    def stop_all(self):
        """Stops limiting all active processes."""
        for p in list(self._active_pids): self.stop(pid=p)

    def shutdown(self):
        """A convenient alias for stop_all()."""
        self.stop_all()

    def get_active(self):
        """Returns a list of actively limited processes."""
        return [info for pid, info in self._process_info.items() if pid in self._active_pids]

    def _get_pids_for_criteria(self, pid=None, process_name=None, window_title_contains=None):
        """Helper to find PIDs matching the given criteria from the managed list."""
        if pid: return [pid] if pid in self._process_info else []
        found_pids = []
        for p, info in self._process_info.items():
            match = False
            if process_name and info["process_name"] == process_name: match = True
            if window_title_contains and info["window_title_contains"] == window_title_contains: match = True
            if match: found_pids.append(p)
        return found_pids