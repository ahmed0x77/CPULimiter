# cpulimiter 🚀

A Python library for Windows to limit the CPU usage of running processes.

## Features ✨

- 🎯 Limit process CPU usage by a specified percentage.
- 🔍 Target processes by Process ID (PID), executable name, or window title.
- 🤝 Manage and control multiple limited processes simultaneously.
- 🛠️ Utility functions to discover running and active processes.

## Installation 📦

```bash
pip install cpulimiter
```

_(Note: This package is not yet published to PyPI.)_

## Quick Start 📖

The following example demonstrates how to limit `chrome.exe` to 5% of CPU usage (a 95% limit).

```python
from cpulimiter import CpuLimiter
import time

# 1. Initialize the limiter
limiter = CpuLimiter()

# 2. Add the process directly by its name.
# The library will find the PID for "chrome.exe" for you.
limiter.add(process_name="chrome.exe", limit_percentage=95)

# 3. Start the limit
# You can also start it by name.
print("Limiting Chrome for 15 seconds...")
limiter.start(process_name="chrome.exe")

time.sleep(15)

# 4. Stop the limit
print("Stopping limit.")
limiter.stop(process_name="chrome.exe")
print("Process limit removed.")
```

## API Reference

### `CpuLimiter` Class

The primary class for managing process limits.

#### `limiter.add(pid, process_name, window_title_contains, limit_percentage)`

Adds a process to the limiter's management list.

- `pid` (int): The Process ID.
- `process_name` (str): The executable name (e.g., `"chrome.exe"`).
- `window_title_contains` (str): A substring to match in a window title.
- `limit_percentage` (int): The percentage by which to limit the CPU (e.g., `95` means the process can use up to 5% of a core).

#### `limiter.start(pid, process_name, window_title_contains)`

Starts the CPU limit on a specific, previously added process.

#### `limiter.stop(pid, process_name, window_title_contains)`

Stops the CPU limit on a specific process.

#### `limiter.start_all()`

Starts the CPU limit on all managed processes.

#### `limiter.stop_all()`

Stops the CPU limit on all managed processes.

### Utility Functions

#### `get_active_window_info()`

Returns a dictionary containing the `pid`, `name`, and `title` of the foreground window.

#### `get_active_app_pids()`

Returns a dictionary of all processes with visible windows.
