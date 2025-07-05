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
LOOP_INTERVAL_SECONDS = 2

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
    "Monitor.exe",
}


def main():
    """Main loop to monitor and save CPU automatically."""
    print("💾 CPU Saver Started!")
    print(f"⚡ Limiting background apps by {LIMIT_PERCENTAGE}% after {INACTIVITY_THRESHOLD_SECONDS} seconds of inactivity")
    print(f"🛡️ Protected system processes: {len(IGNORE_LIST)} processes")
    print("⌨️  Press Ctrl+C to stop\n")

    # Initialize the limiter
    limiter = CpuLimiter()
    last_active_time = {}  # key: process_name, value: last active time
    limited_names = set()  # set of process names currently limited

    try:
        while True:
            current_time = time.time()
            
            # Get current state
            visible_apps = get_active_app_pids()
            active_window = get_active_window_info()
            active_pid = active_window['pid'] if active_window else None
            active_name = None

            # Find the process name for the active PID
            if active_pid:
                active_info = visible_apps.get(active_pid)
                if active_info:
                    active_name = active_info['name']
                    last_active_time[active_name] = current_time

            # Check each visible app
            for pid, app_info in visible_apps.items():
                app_name = app_info['name']
                
                # Skip apps in ignore list (critical system processes)
                if app_name in IGNORE_LIST:
                    continue

                is_currently_active = (app_name == active_name)
                is_currently_limited = (app_name in limited_names)
                
                # Determine if we should limit this app
                if not is_currently_active and not is_currently_limited:
                    time_since_active = current_time - last_active_time.get(app_name, 0)
                    
                    if time_since_active > INACTIVITY_THRESHOLD_SECONDS:
                        print(f"🔒 Saving CPU: Limiting {app_name}")
                        limiter.add(process_name=app_name, limit_percentage=LIMIT_PERCENTAGE)
                        limiter.start(process_name=app_name)
                        limited_names.add(app_name)

                # Remove limit if app becomes active
                elif is_currently_active and is_currently_limited:
                    print(f"🔓 Restoring speed: Unlimiting {app_name}")
                    limiter.stop(process_name=app_name)
                    limited_names.discard(app_name)

            # Clean up limiters for apps that are no longer visible
            names_to_remove = []
            for app_name in limited_names:
                still_visible = any(info['name'] == app_name for info in visible_apps.values())
                if not still_visible:
                    print(f"🧹 Cleaning up limiter for closed app ({app_name})")
                    limiter.stop(process_name=app_name)
                    names_to_remove.append(app_name)
            
            for app_name in names_to_remove:
                limited_names.discard(app_name)

            # Status update every 30 seconds
            if int(current_time) % 30 == 0 and limited_names:
                print(f"📊 CPU Savings: {len(limited_names)} background apps limited: {', '.join(limited_names)}")

            # Wait before next check
            time.sleep(LOOP_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n⚠️  CPU Saver stopped by user")
    
    finally:
        print("🧹 Restoring all apps to full speed...")
        limiter.stop_all()
        print("✅ CPU Saver stopped cleanly")

if __name__ == "__main__":
    main()
