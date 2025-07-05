from cpulimiter import CpuLimiter
import time
import psutil

def find_pid_by_name(process_name):
    """Helper function to find a PID by its name."""
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            return proc.info['pid']
    return None

# --- Example Usage ---

# 1. Initialize the limiter
limiter = CpuLimiter()

# 2. Find a process to limit (e.g., Notepad)
#    (You can open Notepad to test this)
notepad_pid = find_pid_by_name("notepad.exe")

if notepad_pid:
    print(f"Found Notepad with PID: {notepad_pid}")

    # 3. Add the process to the limiter
    limiter.add(pid=notepad_pid, limit_percentage=95)

    # 4. Start limiting
    print("Starting to limit Notepad for 15 seconds...")
    limiter.start(pid=notepad_pid)

    # You can check the task manager to see the effect.
    time.sleep(15)

    # 5. Stop limiting
    print("Stopping the limit.")
    limiter.stop(pid=notepad_pid)

    print("Limiting has been stopped.")
else:
    print("Notepad is not running. Please open it and run the script again.")

# --- Example with multiple processes ---

# limiter.add(process_name="chrome.exe", limit_percentage=90)
# limiter.add(process_name="spotify.exe", limit_percentage=80)

# print("\nStarting to limit multiple applications...")
# limiter.start_all()
# time.sleep(20)
# print("Stopping all limits.")
# limiter.stop_all()
