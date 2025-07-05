import sys
import os
import ctypes
import ctypes.wintypes
import pygetwindow as gw
import win32process
import psutil
import time
import threading

# --- CONFIGURATION ---
# How much to limit the CPU by (98 = limit by 98%, leaving 2% for the app).
LIMIT_PERCENTAGE = 98
# How many seconds of inactivity before an app is limited.
INACTIVITY_THRESHOLD_SECONDS = 10
# How often the script checks for active/inactive apps (in seconds).
LOOP_INTERVAL_SECONDS = 3
# List of process names to ignore. Prevents throttling important or self-referential apps.
IGNORE_LIST = {
    "explorer.exe",         # Windows Explorer (taskbar, etc.)
    "svchost.exe",          # Critical Windows service host
    "powershell.exe",       # The console you might be running the script in
    "cmd.exe",              # The other console you might be running in
    "WindowsTerminal.exe",  # The new Windows Terminal
    "python.exe",           # The script interpreter itself
    "conhost.exe"           # Console Window Host
}
# --- END CONFIGURATION ---
ALLOW_LIST = {
    "PopSQL.exe",
    "chrome.exe",
}

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

class CPULimiter:
    def __init__(self, pid, limit_percentage):
        self.pid = pid
        self.limit_percentage = limit_percentage
        self.active = False
        self.thread = None
        self.stop_event = threading.Event()
        self._thread_handles = {}  # Cache thread handles
        self._last_thread_update = 0
        
    def start(self):
        """Start limiting the CPU usage of the process."""
        if not self.active:
            self.active = True
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._limit_loop)
            self.thread.daemon = True
            self.thread.start()
            
    def stop(self):
        """Stop limiting the CPU usage of the process."""
        if self.active:
            self.active = False
            self.stop_event.set()
            # Resume all threads before stopping
            self._resume_all_threads()
            if self.thread:
                self.thread.join(timeout=2)
                
    def _get_thread_ids(self):
        """Get all thread IDs for the process."""
        try:
            process = psutil.Process(self.pid)
            return [thread.id for thread in process.threads()]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []
    
    def _get_or_create_handle(self, tid):
        """Get cached thread handle or create new one."""
        if tid not in self._thread_handles:
            handle = OpenThread(THREAD_SUSPEND_RESUME, False, tid)
            if handle:
                self._thread_handles[tid] = handle
        return self._thread_handles.get(tid)
    
    def _cleanup_handles(self):
        """Close all cached handles."""
        for handle in self._thread_handles.values():
            CloseHandle(handle)
        self._thread_handles.clear()
            
    def _suspend_all_threads(self):
        """Suspend all threads of the process."""
        for tid in self._get_thread_ids():
            handle = self._get_or_create_handle(tid)
            if handle:
                SuspendThread(handle)
                
    def _resume_all_threads(self):
        """Resume all threads of the process."""
        for tid in self._get_thread_ids():
            handle = self._get_or_create_handle(tid)
            if handle:
                ResumeThread(handle)
                
    def _limit_loop(self):
        """Main loop that limits CPU by suspending/resuming threads."""
        # Use even longer cycle time to reduce CPU usage
        cycle_time = 5.0  # 5 second cycle for minimal CPU usage
        suspend_time = cycle_time * (self.limit_percentage / 100.0)
        resume_time = cycle_time - suspend_time
        
        while self.active and not self.stop_event.is_set():
            try:
                # Only update thread list every 30 seconds
                current_time = time.time()
                if current_time - self._last_thread_update > 30:
                    self._cleanup_handles()
                    self._last_thread_update = current_time
                
                # Suspend threads for calculated time
                self._suspend_all_threads()
                self.stop_event.wait(suspend_time)
                
                if not self.active:
                    break
                    
                # Resume threads for calculated time
                self._resume_all_threads()
                self.stop_event.wait(resume_time)
                
            except Exception as e:
                print(f"Error in limit loop for PID {self.pid}: {e}")
                break
                
        # Make sure threads are resumed when we exit
        self._resume_all_threads()
        self._cleanup_handles()

def get_visible_app_pids():
    """Gets the PID and Name for applications with a visible window."""
    visible_apps = {}
    for window in gw.getAllWindows():
        if window.visible and window.title:
            try:
                hwnd = window._hWnd
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid not in visible_apps and pid != os.getpid():
                    process_name = psutil.Process(pid).name()
                    visible_apps[pid] = process_name
            except (psutil.NoSuchProcess, psutil.AccessDenied, gw.PyGetWindowException):
                continue
    return visible_apps

def main():
    """Main loop to monitor and throttle applications."""
    print("--- CPU Auto-Throttle Script Started ---")
    print(f"Limiting inactive apps by {LIMIT_PERCENTAGE}% after {INACTIVITY_THRESHOLD_SECONDS} seconds.")
    print("Press Ctrl+C to stop.")

    limiters = {}
    last_active_time = {}
    last_window_check = 0
    cached_visible_apps = {}
    cached_active_pid = None

    try:
        while True:
            current_time = time.time()
            
            # Only check windows every 5 seconds to reduce CPU usage
            if current_time - last_window_check >= 5:
                active_window = gw.getActiveWindow()
                cached_visible_apps = get_visible_app_pids()
                last_window_check = current_time
                
                if active_window:
                    try:
                        _, cached_active_pid = win32process.GetWindowThreadProcessId(active_window._hWnd)
                        last_active_time[cached_active_pid] = current_time
                    except Exception:
                        cached_active_pid = None
                else:
                    cached_active_pid = None
            
            # Use cached values
            visible_apps = cached_visible_apps
            active_pid = cached_active_pid

            # --- Step 1: Decide which apps to LIMIT ---
            for pid, name in visible_apps.items():
                # Only limit apps in our allow list
                if name not in ALLOW_LIST:
                    continue

                is_active = (pid == active_pid)
                is_limited = pid in limiters
                
                if not is_limited and not is_active:
                    time_since_active = current_time - last_active_time.get(pid, 0)
                    if time_since_active > INACTIVITY_THRESHOLD_SECONDS:
                        print(f"Limiting inactive app: {name} (PID: {pid})")
                        limiter = CPULimiter(pid, LIMIT_PERCENTAGE)
                        limiter.start()
                        limiters[pid] = limiter

            # --- Step 2: DISABLED FOR TESTING - Keep all apps limited ---
            # Comment out unlimiting logic to test if limiting works
            for pid in list(limiters.keys()):
                app_is_visible = pid in visible_apps
                is_now_active = (pid == active_pid)
                
                if is_now_active or not app_is_visible:
                    limiter = limiters.pop(pid)
                    print(f"Unlimiting app: {visible_apps.get(pid, 'N/A')} (PID: {pid})")
                    limiter.stop()
                    
                    if is_now_active:
                        last_active_time[pid] = current_time
            
            # Show current limited apps only occasionally
            if limiters and int(current_time) % 10 == 0:
                print(f"Currently limiting {len(limiters)} apps: {[visible_apps.get(pid, 'Unknown') for pid in limiters.keys()]}")

            # Longer sleep to reduce main loop CPU usage
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
    finally:
        print("Cleaning up and stopping all limiters...")
        for pid, limiter in limiters.items():
            try:
                print(f"  - Stopping limiter for PID {pid}")
                limiter.stop()
            except Exception:
                pass
        print("--- CPU Auto-Throttle Script Stopped ---")

def is_admin():
    """Checks if the script is running with Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    if is_admin():
        main()
    else:
        print("Admin rights required. Attempting to re-launch with elevation...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)


