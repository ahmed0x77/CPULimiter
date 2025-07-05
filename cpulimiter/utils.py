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
