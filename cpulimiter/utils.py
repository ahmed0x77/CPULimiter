import pygetwindow as gw
import win32process
import psutil

def get_active_app_pids():
    """
    Gets the PID and Name for applications with a visible window.
    This mimics the simple view of the Windows Task Manager.
    """
    active_apps = {}
    
    for window in gw.getAllWindows():
        if window.visible and window.title:
            
            # Get the window's handle (HWND)
            hwnd = window._hWnd
            
            # From the handle, get the Process ID (PID)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            if pid not in active_apps:
                try:
                    # Get the process name from the PID for a cleaner output
                    process_name = psutil.Process(pid).name()
                    active_apps[pid] = {
                        'name': process_name,
                        'title': window.title
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Handle cases where the process ends before we can get its name
                    continue

    return active_apps


def get_active_window_info():
    """
    Gets information about the currently active (foreground) window.
    Returns a dictionary with 'pid', 'name', and 'title', or None if no active window.
    """
    try:
        active_window = gw.getActiveWindow()
        if active_window:
            hwnd = active_window._hWnd
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process_name = psutil.Process(pid).name()
            return {
                'pid': pid,
                'name': process_name,
                'title': active_window.title
            }
    except (gw.PyGetWindowException, psutil.NoSuchProcess, psutil.AccessDenied):
        # Handle cases where window disappears or process is inaccessible
        return None
    return None

def emergency_resume_chrome():
    """
    Attempts to force resume all Chrome processes using NtResumeProcess.
    This is a last resort to recover unresponsive Chrome instances.
    """
    import ctypes
    from ctypes import wintypes
    import psutil

    # Load ntdll.dll to access NtResumeProcess
    ntdll = ctypes.WinDLL('ntdll')
    NtResumeProcess = ntdll.NtResumeProcess
    NtResumeProcess.argtypes = [wintypes.HANDLE]
    NtResumeProcess.restype = wintypes.DWORD

    # Find all Chrome processes
    chrome_pids = [p.pid for p in psutil.process_iter(['pid', 'name']) 
                if 'chrome' in p.info['name'].lower()]

    print(f"Found {len(chrome_pids)} Chrome processes - attempting to force resume...")

    # Try to resume each Chrome process directly
    for pid in chrome_pids:
        try:
            # Open the process with full access rights
            process_handle = ctypes.windll.kernel32.OpenProcess(
                0x1FFFFF,  # PROCESS_ALL_ACCESS
                False,
                pid
            )
            
            if process_handle:
                # Call NtResumeProcess directly
                status = NtResumeProcess(process_handle)
                print(f"PID {pid}: Resume status {status}")
                ctypes.windll.kernel32.CloseHandle(process_handle)
            else:
                print(f"Could not open PID {pid}")
        except Exception as e:
            print(f"Error with PID {pid}: {e}")

    print("Attempted to force-resume all Chrome processes.")
    print("Chrome should become responsive within a few seconds.")