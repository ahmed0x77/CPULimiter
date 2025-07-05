from cpulimiter import CpuLimiter
import time


# --- Example Usage ---

# 1. Initialize the limiter
limiter = CpuLimiter()

app_name = "notepad.exe"

# 3. Add the process to the limiter
limiter.add(process_name=app_name, limit_percentage=95)

# 4. Start limiting
print("Starting to limit Notepad for 15 seconds...")
limiter.start(process_name=app_name)

# You can check the task manager to see the effect.
time.sleep(15)

# 5. Stop limiting
print("Stopping the limit.")
limiter.stop(process_name=app_name)

print("Limiting has been stopped.")

# --- Example with multiple processes ---

# limiter.add(process_name="chrome.exe", limit_percentage=90)
# limiter.add(process_name="spotify.exe", limit_percentage=80)

# print("\nStarting to limit multiple applications...")
# limiter.start_all()
# time.sleep(20)
# print("Stopping all limits.")
# limiter.stop_all()
