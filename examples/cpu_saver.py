"""
CPU Saver - Automatic Background App Limiter

This example automatically saves CPU by limiting background applications when they 
become inactive. It gives full priority to whatever application you're currently using
while throttling everything else that's running in the background.

Perfect for:
- Gaming (limit background apps while gaming)
- Work (focus CPU on your active application)  
- Battery saving (reduce overall system load)
- Performance optimization

Requirements:
- Administrator privileges (the script will try to restart itself with admin rights)
- cpulimiter library: pip install cpulimiter
"""

import sys
import ctypes
import time
from cpulimiter import CpuLimiter, get_active_app_pids, get_active_window_info

# --- CONFIGURATION ---
# How much to limit the CPU by (98 = limit by 98%, leaving 2% for the app)
LIMIT_PERCENTAGE = 98

# How many seconds of inactivity before an app is limited
INACTIVITY_THRESHOLD_SECONDS = 10

# How often the script checks for active/inactive apps (in seconds)
LOOP_INTERVAL_SECONDS = 5

# List of process names to ignore (critical system processes and tools)
IGNORE_LIST = {
    "explorer.exe",         # Windows Explorer (taskbar, etc.)
    "svchost.exe",          # Critical Windows service host
    "powershell.exe",       # PowerShell console
    "cmd.exe",              # Command prompt
    "WindowsTerminal.exe",  # Windows Terminal
    "python.exe",           # Python interpreter
    "conhost.exe",          # Console Window Host
    "dwm.exe",             # Desktop Window Manager
    "winlogon.exe",        # Windows Logon Process
    "csrss.exe",           # Client/Server Runtime
}

def is_admin():
    """Checks if the script is running with Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    """Main loop to monitor and save CPU automatically."""
    print("💾 CPU Saver Started!")
    print(f"⚡ Limiting background apps by {LIMIT_PERCENTAGE}% after {INACTIVITY_THRESHOLD_SECONDS} seconds of inactivity")
    print(f"🛡️ Protected system processes: {len(IGNORE_LIST)} processes")
    print("⌨️  Press Ctrl+C to stop\n")

    # Initialize the limiter
    limiter = CpuLimiter()
    last_active_time = {}
    limited_pids = set()

    try:
        while True:
            current_time = time.time()
            
            # Get current state
            visible_apps = get_active_app_pids()
            active_window = get_active_window_info()
            active_pid = active_window['pid'] if active_window else None
            
            # Update last active time for the currently active app
            if active_pid:
                last_active_time[active_pid] = current_time

            # Check each visible app
            for pid, app_info in visible_apps.items():
                app_name = app_info['name']
                
                # Skip apps in ignore list (critical system processes)
                if app_name in IGNORE_LIST:
                    continue

                is_currently_active = (pid == active_pid)
                is_currently_limited = pid in limited_pids
                
                # Determine if we should limit this app
                if not is_currently_active and not is_currently_limited:
                    time_since_active = current_time - last_active_time.get(pid, 0)
                    
                    if time_since_active > INACTIVITY_THRESHOLD_SECONDS:
                        print(f"🔒 Saving CPU: Limiting {app_name} (PID: {pid})")
                        limiter.add(pid=pid, limit_percentage=LIMIT_PERCENTAGE)
                        limiter.start(pid=pid)
                        limited_pids.add(pid)

                # Remove limit if app becomes active
                elif is_currently_active and is_currently_limited:
                    print(f"🔓 Restoring speed: Unlimiting {app_name} (PID: {pid})")
                    limiter.stop(pid=pid)
                    limited_pids.discard(pid)

            # Clean up limiters for apps that are no longer visible
            pids_to_remove = []
            for pid in limited_pids:
                if pid not in visible_apps:
                    print(f"🧹 Cleaning up limiter for closed app (PID: {pid})")
                    limiter.stop(pid=pid)
                    pids_to_remove.append(pid)
            
            for pid in pids_to_remove:
                limited_pids.discard(pid)

            # Status update every 30 seconds
            if int(current_time) % 30 == 0 and limited_pids:
                limited_apps = [visible_apps.get(pid, {}).get('name', 'Unknown') for pid in limited_pids]
                print(f"📊 CPU Savings: {len(limited_pids)} background apps limited: {', '.join(limited_apps)}")

            # Wait before next check
            time.sleep(LOOP_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n⚠️  CPU Saver stopped by user")
    
    finally:
        print("🧹 Restoring all apps to full speed...")
        limiter.stop_all()
        print("✅ CPU Saver stopped cleanly")

if __name__ == "__main__":
    # Check for admin privileges
    if not is_admin():
        print("🔐 Administrator privileges required for CPU Saver")
        print("🔄 Attempting to restart with elevated privileges...")
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
        except Exception as e:
            print(f"❌ Failed to restart with admin privileges: {e}")
            print("💡 Please run this script as Administrator manually")
        sys.exit(1)
    else:
        print("✅ Running with Administrator privileges")
        main()
