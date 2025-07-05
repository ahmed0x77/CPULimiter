from cpulimiter import CpuLimiter
import time

# --- Example: Modifying a CPU Limit ---

# 1. Initialize the limiter
limiter = CpuLimiter()

# 2. Add notepad.exe and limit it to 10% CPU (a 90% limit)
# You can open notepad.exe to see this in action.
print("Opening notepad.exe and limiting it to 10% CPU...")
limiter.add(process_name="notepad.exe", limit_percentage=90)
limiter.start_all()

# Keep the initial limit for 10 seconds
print("Limit will be active for 10 seconds.")
time.sleep(10)

# 3. Modify the limit to 50% CPU using the dedicated `modify_limit` method
print("\nModifying limit to 50% CPU using modify_limit()...")
limiter.modify_limit(process_name="notepad.exe", new_limit_percentage=50)

# Keep the new limit for another 10 seconds
print("New limit will be active for 10 seconds.")
time.sleep(10)

# 4. You can also use the `add` method to modify the limit.
# This is a convenient shortcut.
print("\nModifying limit back to 20% CPU using add()...")
limiter.add(process_name="notepad.exe", limit_percentage=80) # 80% limit = 20% CPU

# Keep the final limit for 10 seconds
print("Final limit will be active for 10 seconds.")
time.sleep(10)

# 5. Stop the limiter
limiter.shutdown()
print("\nLimiter has been shut down. Notepad is back to normal.")
