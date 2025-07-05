"""
Simple CPU Limiting Example

This example shows how to manually limit specific applications using the cpulimiter library.
Perfect for beginners who want to understand the basic functionality.

Usage:
1. Install: pip install cpulimiter
2. Run this script as Administrator
3. The script will limit Chrome and Spotify to 10% CPU usage
"""

from cpulimiter import CpuLimiter
import time

def main():
    print("🚀 Simple CPU Limiter Example")
    print("=" * 40)

    # With the updated library, you can define and start the limits all in one step.
    # The keys are the process identifiers (name, PID, or window title substring)
    # and the values are the percentage to limit by.
    processes_to_limit = {
        "chrome.exe": 90,       # Limit Chrome to 10% CPU (90% limit)
        "spotify.exe": 95,      # Limit Spotify to 5% CPU (95% limit)
        "YouTube": 85           # Limit any window with "YouTube" in the title to 15% CPU
    }

    print("📝 Initializing and starting limiter for:")
    for proc, limit in processes_to_limit.items():
        print(f"   ✅ {proc} (limited by {limit}%)")

    # Initialize the limiter and it will automatically start limiting the processes.
    limiter = CpuLimiter(processes_to_limit)

    print("\n🔄 CPU limiting is now active...")
    print("💡 Check Task Manager to see the effect!")
    print("⌨️  Press Ctrl+C to stop\n")

    try:
        # Let it run and show status every 10 seconds
        while True:
            time.sleep(10)
            active_limits = limiter.get_active()
            if active_limits:
                print(f"📊 Status: {len(active_limits)} processes are being actively limited.")
            else:
                print("💡 No target processes found. Make sure they are running.")
                break

    except KeyboardInterrupt:
        print("\n⚠️  Stopping due to user interrupt...")

    finally:
        print("🛑 Stopping all CPU limits...")
        limiter.shutdown() # shutdown() is an alias for stop_all()
        print("✅ All limits removed. Applications restored to normal speed.")


def is_admin():
    """Checks if the script is running with Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    import ctypes
    import sys
    if is_admin():
        main()
    else:
        print("Admin rights required. Attempting to re-launch with elevation...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)