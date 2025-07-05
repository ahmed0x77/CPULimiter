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






def get_non_critical_processes():
    """
    Gets PID and Name for running processes, ignoring critical system ones
    that could crash Windows or severely disrupt its functionality if terminated.
    """


    CRITICAL_PROCESSES = {
        # --- Existing Core System Processes ---
        'system idle process',
        'system',
        'smss.exe',          # Session Manager Subsystem
        'csrss.exe',         # Client/Server Runtime Subsystem
        'wininit.exe',       # Windows Initialization Process
        'winlogon.exe',      # Windows Logon Application
        'lsass.exe',         # Local Security Authority Subsystem Service
        'services.exe',      # Service Control Manager
        'svchost.exe',       # Service Host (hosts many Windows services)
        'dwm.exe',           # Desktop Window Manager
        'explorer.exe',      # Windows Shell (Taskbar, Desktop, etc.) - killing this is highly disruptive

        # --- New additions from your list and common critical processes ---

        # System Processes (core to Windows OS, drivers, security, etc.)
        'registry',          # Pseudo-process for kernel registry access (critical!)
        'lsaiso.exe',        # Local Security Authority Isolated process (security critical)
        'fontdrvhost.exe',   # Font Driver Host (essential for rendering text)
        'wudfhost.exe',      # Windows User-Mode Driver Framework Host (for many drivers)
        'runtimebroker.exe', # Windows process for UWP apps, permissions (essential for modern apps)
        'taskhostw.exe',     # Windows Host Process for Background Tasks
        'dashost.exe',       # Device Association Framework Provider Host
        'conhost.exe',       # Console Window Host (for command prompt, PowerShell, many apps)
        'nlsvc.exe',         # Network Location Awareness Service (network profiles)
        'wlanext.exe',       # WLAN AutoConfig Extensibility Module (Wi-Fi management)
        'securityhealthservice.exe', # Windows Security Center service
        'wsccommunicator.exe', # Windows Security Center Communicator
        'wmiprvse.exe',      # WMI Provider Host (Windows Management Instrumentation - many apps rely on it)
        'vmmem',             # Hyper-V/WSL2 VM process (killing it kills the VM, which is often not desired)
        'startmenuexperiencehost.exe', # Start Menu process (killing breaks Start Menu)
        'comppkgsrv.exe',    # Component Package Server (Windows updates/servicing)
        'ctfmon.exe',        # CTF Loader (input method editor, language bar)
        'sgrmbroker.exe',    # System Guard Runtime Monitor Broker (Windows security)
        'settingsynchost.exe', # Windows Settings Sync Host
        'uhssvc.exe',        # Update Health Tools Service (Windows updates)
        'searchapp.exe',     # Windows Search Application (for desktop search)
        'sihost.exe',        # Shell Infrastructure Host (important for shell extensions, desktop)
        'shellexperiencehost.exe', # Hosts parts of Windows shell (notifications, action center)
        'rundll32.exe',      # Executes DLL functions (often used by system processes, risky to kill)
        'audiodg.exe',       # Windows Audio Device Graph Isolation (essential for audio)
        'dllhost.exe',       # COM Surrogate (hosts COM+ objects, essential for various apps)
        'textinputhost.exe', # Input Method Editor (IME) Host (keyboard input)

        # Security Software Components (BitDefender in your case - vital for protection)
        # While not directly Windows, killing these leaves your system vulnerable and can trigger self-protection.
        'bduserhost.exe',
        'bdservicehost.exe',
        'bdparentalservice.exe',
        'bdntwrk.exe',
        'bdagent.exe',
        'bdredline.exe',

        # Graphics Card Related (NVIDIA in your case - critical for display functionality)
        # Killing these can result in a black screen, unrecoverable display issues without reboot.
        'nvdisplay.container.exe',
        'nvcontainer.exe',
        'nvbroadcast.container.exe',
        'nvidia web helper.exe', # Often associated with NVIDIA services
        'cmd.exe', 
    }

    user_procs = {}
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # Convert the process name to lowercase for case-insensitive comparison
            process_name_lower = proc.info['name'].lower()
            
            # Check if the process name is in our CRITICAL_PROCESSES set
            if process_name_lower not in CRITICAL_PROCESSES:
                user_procs[proc.info['pid']] = {'name': proc.info['name']}
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass # Ignore processes that disappear, are denied access, or are zombies
    return user_procs
