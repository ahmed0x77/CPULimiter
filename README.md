# cpulimiter 🌡️

[![PyPI version](https://img.shields.io/pypi/v/cpulimiter.svg)](https://pypi.org/project/cpulimiter/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/cpulimiter.svg)](https://pypi.org/project/cpulimiter/)
[![PyPI license](https://img.shields.io/pypi/l/cpulimiter.svg)](https://github.com/Ahmed-Ashraf-dv/CPULimiter/blob/main/LICENSE)

A simple, lightweight Python library for Windows to limit and control the CPU usage of any running process.

## 📖 Quick Start

Limit all `chrome.exe` processes to just 5% of a single CPU core's power.

```python
from cpulimiter import CpuLimiter
import time

# 1. Find all "chrome.exe" processes and limit them by 95% (allowing 5% usage).
limiter = CpuLimiter({"chrome.exe": 95})

# 2. The limiter runs in the background. Let's see the effect for 15 seconds.
print("Limiting Chrome's CPU usage for 15 seconds...")
time.sleep(15)

# 3. To stop limiting, simply call the shutdown() method.
limiter.shutdown()
print("CPU limit removed. Chrome is back to normal.")
```

_You can check your Task Manager to see the effect in real-time!_

## 🤔 Why Use cpulimiter?

Have you ever had a program consume 100% of your CPU, making your system unresponsive and your fans spin like a jet engine? `cpulimiter` solves this by throttling the application, which is perfect for:

- 🎮 **Gaming:** Cap the CPU usage of a game to prevent overheating without quitting.
- 🌐 **Browsing:** Limit resource-hungry browsers like Chrome or Edge when you have many tabs open.
- 💼 **Background Tasks:** Run heavy data processing or video encoding in the background without it slowing down your main work.
- 🔋 **Saving Battery:** Reduce power consumption on laptops by reining in demanding applications.
- 🤫 **Quieting Fans:** Keep your machine quiet by preventing CPU usage spikes.

## ✨ Features

- 🎯 **Limit CPU Usage:** Throttle process CPU usage to a specific percentage.
- 🔍 **Flexible Targeting:** Target processes by Process ID (PID), executable name (`"chrome.exe"`), or even window title.
- 🤝 **Multi-Process Management:** Control and limit multiple processes at the same time.
- 🛠️ **Process Discovery:** Includes utility functions to find running applications and the active foreground window.
- 🕊️ **Lightweight:** Built on a high-performance C++ engine with a minimal performance footprint.

## 📦 Installation

```bash
pip install cpulimiter
```

## ⚙️ How It Works

The secret to `cpulimiter`'s high performance and low overhead is its **native C++ engine**.

Instead of complex calculations, it uses a simple but powerful technique: rapidly **pausing** and **resuming** the entire target application. To achieve a 90% limit, the engine might pause the process for 180 milliseconds and then let it run for 20 milliseconds. This cycle happens so quickly that the application remains responsive, but its total CPU time is drastically reduced.

This project is inspired by the classic utility BES (Battle Encoder Shirasé), but is designed to be a modern and **significantly more lightweight** alternative. By using a minimal, highly-optimized C++ engine, `cpulimiter` avoids the overhead found in older tools, making it exceptionally efficient.

## 📚 Examples

Check out the `examples/` folder for more advanced use cases:

- **`basic_usage.py`** - A simple, manual introduction to the library's methods.
- **`simple_limit.py`** - Manually limit a list of specific applications.
- **`cpu_saver.py`** - An automatic CPU saver that throttles all applications that are not in the foreground.
- **`cpu_saver_GUI.pyw`** - A modern graphical app for automatically limiting CPU usage of background applications, with custom rules, ignore list, and system tray support.
- **`advanced_interactive.py`** - An interactive command-line tool for real-time process management.
- **`modify_limit_example.py`** - Demonstrates how to change the CPU limit of a process that is already being managed.

## API Reference

### `CpuLimiter` Class

The primary class for managing process limits.

#### `limiter.add(pid, process_name, window_title_contains, limit_percentage)`

Adds a process to the limiter's management list. If the process is already managed, this will update its CPU limit percentage.

- `pid` (int): The Process ID.
- `process_name` (str): The executable name (e.g., `"chrome.exe"`).
- `window_title_contains` (str): A substring to match in a window title.
- `limit_percentage` (int): The percentage by which to limit the CPU (e.g., `95` means the process can use up to 5% of a core).

#### `limiter.modify_limit(pid, process_name, window_title_contains, new_limit_percentage)`

Modifies the CPU limit for a process that is already being actively limited.

- `pid`, `process_name`, `window_title_contains`: Identifiers for the process to modify.
- `new_limit_percentage` (int): The new limit to apply.

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

Returns a dictionary of all processes with visible windows, mapping their PIDs to their executable names.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/Ahmed-Ashraf-dv/CPULimiter/issues).

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🛠️ Legacy Version

In addition to the main `cpulimiter` library, which uses a high-performance C++ backend, there is also a **legacy version** available in `limiter_legacy.py`. This version is written entirely in Python and does not require any DLL files.

### When to Use the Legacy Version?

The legacy version might be suitable for specific use cases, such as:

- **Media Applications**: Limiting CPU usage for processes like video players or music players without causing issues like cracked or distorted sound.
- **No DLL Dependency**: If you prefer not to use the C++ backend or cannot load the DLL file for any reason.

### Key Differences

| Feature | Main Version (C++) | Legacy Version (Python) |
| :--------------------- | :------------------------- | :----------------------- |
| **Performance** | Minimal CPU usage (near-zero). | May use more CPU due to Python overhead. |
| **Dependency** | Requires `limiter_engine.dll`. | No external dependencies. |
| **Precision** | High precision via native timers. | Slightly less precise. |
| **Use Case** | General-purpose CPU limiting. | Media apps or environments without DLL support. |

To use the legacy version, simply import the `limiter_legacy` module and then use its `CpuLimiter` class:

```python
from cpulimiter.limiter_legacy import CpuLimiter

# Note: You are now using the Python-based legacy limiter
limiter = CpuLimiter({"chrome.exe": 90})

# ... rest of your code
```
