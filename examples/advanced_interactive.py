"""
Advanced CPU Limiter Example

This example demonstrates advanced features of the cpulimiter library:
- Targeting processes by different methods (PID, name, window title)
- Individual process control
- Real-time monitoring and adjustment
- Dynamic process discovery
"""

from cpulimiter import CpuLimiter, get_active_app_pids, get_active_window_info
import time
import sys

def show_available_apps():
    """Display all currently running applications with visible windows."""
    print("🔍 Scanning for running applications...")
    apps = get_active_app_pids()
    
    if not apps:
        print("❌ No applications with visible windows found")
        return
    
    print(f"📱 Found {len(apps)} applications:")
    print("-" * 50)
    for pid, info in apps.items():
        print(f"  PID: {pid:6} | {info['name']:20} | {info['title'][:30]}...")
    print("-" * 50)

def interactive_limiting():
    """Interactive mode where user can select applications to limit."""
    limiter = CpuLimiter()
    
    while True:
        print("\n🎛️  INTERACTIVE CPU LIMITER")
        print("1. 📋 Show running applications")
        print("2. 🎯 Limit application by name")
        print("3. 🔢 Limit application by PID")
        print("4. 🖼️  Limit by window title (contains)")
        print("5. 📊 Show current limits")
        print("6. 🛑 Stop specific limit")
        print("7. 🛑 Stop all limits")
        print("8. 🚪 Exit")
        
        choice = input("\nSelect option (1-8): ").strip()
        
        if choice == "1":
            show_available_apps()
            
        elif choice == "2":
            name = input("Enter process name (e.g., chrome.exe): ").strip()
            if name:
                try:
                    limit = int(input("Enter limit percentage (1-99): "))
                    limiter.add(process_name=name, limit_percentage=limit)
                    limiter.start(process_name=name)
                    print(f"✅ Started limiting {name} by {limit}%")
                except ValueError:
                    print("❌ Invalid percentage")
                    
        elif choice == "3":
            try:
                pid = int(input("Enter PID: "))
                limit = int(input("Enter limit percentage (1-99): "))
                limiter.add(pid=pid, limit_percentage=limit)
                limiter.start(pid=pid)
                print(f"✅ Started limiting PID {pid} by {limit}%")
            except ValueError:
                print("❌ Invalid PID or percentage")
                
        elif choice == "4":
            title = input("Enter window title substring: ").strip()
            if title:
                try:
                    limit = int(input("Enter limit percentage (1-99): "))
                    limiter.add(window_title_contains=title, limit_percentage=limit)
                    limiter.start(window_title_contains=title)
                    print(f"✅ Started limiting windows containing '{title}' by {limit}%")
                except ValueError:
                    print("❌ Invalid percentage")
                    
        elif choice == "5":
            active = limiter.get_active()
            if active:
                print(f"\n📊 Currently limiting {len(active)} processes:")
                for proc in active:
                    print(f"  - PID: {proc['pid']}, Limit: {proc['limit_percentage']}%")
            else:
                print("📊 No processes currently being limited")
                
        elif choice == "6":
            method = input("Stop by (name/pid): ").strip().lower()
            if method == "name":
                name = input("Enter process name: ").strip()
                limiter.stop(process_name=name)
                print(f"🛑 Stopped limiting {name}")
            elif method == "pid":
                try:
                    pid = int(input("Enter PID: "))
                    limiter.stop(pid=pid)
                    print(f"🛑 Stopped limiting PID {pid}")
                except ValueError:
                    print("❌ Invalid PID")
                    
        elif choice == "7":
            limiter.stop_all()
            print("🛑 Stopped all limits")
            
        elif choice == "8":
            limiter.stop_all()
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice")

def auto_monitor_mode():
    """Automatically monitor and display the currently active application."""
    print("🔄 AUTO-MONITOR MODE")
    print("This mode will show you which application is currently active")
    print("Press Ctrl+C to return to main menu\n")
    
    try:
        while True:
            active = get_active_window_info()
            if active:
                print(f"🎯 Active: {active['name']} (PID: {active['pid']}) - {active['title'][:50]}...")
            else:
                print("❓ No active window detected")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n🔙 Returning to main menu...")

def main():
    print("🚀 ADVANCED CPU LIMITER")
    print("=" * 50)
    
    while True:
        print("\n🎛️  MAIN MENU")
        print("1. 🎮 Interactive Limiting Mode")
        print("2. 👁️  Auto-Monitor Mode (see active apps)")
        print("3. 📋 Quick App List")
        print("4. 🚪 Exit")
        
        choice = input("\nSelect mode (1-4): ").strip()
        
        if choice == "1":
            interactive_limiting()
        elif choice == "2":
            auto_monitor_mode()
        elif choice == "3":
            show_available_apps()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    import ctypes
    
    # Check for admin privileges
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    
    if not is_admin:
        print("🔐 Administrator privileges required")
        print("🔄 Please run as Administrator")
        input("Press Enter to exit...")
        sys.exit(1)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Program interrupted by user")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        input("Press Enter to exit...")
