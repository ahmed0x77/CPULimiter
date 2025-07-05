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
    
    # Initialize the limiter
    limiter = CpuLimiter()
    
    # Add applications to limit
    # This will find all running instances and limit them
    print("📝 Adding applications to limit...")
    
    # Limit Chrome to 10% CPU (90% limitation)
    limiter.add(process_name="chrome.exe", limit_percentage=90)
    print("   ✅ Added Chrome (chrome.exe) - 90% limitation")
    
    # Limit Spotify to 5% CPU (95% limitation) 
    limiter.add(process_name="spotify.exe", limit_percentage=95)
    print("   ✅ Added Spotify (spotify.exe) - 95% limitation")
    
    # You can also limit by window title
    limiter.add(window_title_contains="YouTube", limit_percentage=85)
    print("   ✅ Added YouTube windows - 85% limitation")
    
    print("\n🔄 Starting CPU limiting...")
    print("💡 Check Task Manager to see the effect!")
    print("⌨️  Press Ctrl+C to stop\n")
    
    # Start limiting all added processes
    limiter.start_all()
    
    try:
        # Let it run and show status every 10 seconds
        for i in range(6):  # Run for 60 seconds total
            time.sleep(10)
            active_limits = limiter.get_active()
            print(f"📊 Status update #{i+1}: {len(active_limits)} processes being limited")
            
            if not active_limits:
                print("💡 No processes found to limit. Make sure the target applications are running.")
    
    except KeyboardInterrupt:
        print("\n⚠️  Stopping early due to user interrupt...")
    
    finally:
        print("🛑 Stopping all CPU limits...")
        limiter.stop_all()
        print("✅ All limits removed. Applications restored to normal speed.")

if __name__ == "__main__":
    import ctypes
    import sys
    
    # Check for admin privileges
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    
    if not is_admin:
        print("🔐 This script requires Administrator privileges")
        print("🔄 Please run as Administrator and try again")
        input("Press Enter to exit...")
        sys.exit(1)
    
    main()
