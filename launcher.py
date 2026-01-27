#!/usr/bin/env python3
"""
WinstyleS Launcher
Entry point for the packaged application.
"""

import sys
import os

# When running as a bundled executable, add the correct paths
if getattr(sys, 'frozen', False):
    # Running as compiled
    bundle_dir = sys._MEIPASS
    # Add the bundle directory to path so imports work
    sys.path.insert(0, bundle_dir)
else:
    # Running as script
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

def main():
    """Launch the WinstyleS GUI."""
    # Determine which GUI to launch
    # Priority: Web UI (more modern), fallback to CustomTkinter
    
    print("正在启动 WinstyleS...")
    
    try:
        # Try to import and run the web UI
        from start_web_ui import run_server
        run_server()
    except ImportError:
        # Fallback to CustomTkinter GUI
        try:
            from winstyles.gui.app import WinstyleSApp
            app = WinstyleSApp()
            app.mainloop()
        except ImportError as e:
            print(f"无法启动 GUI: {e}")
            print("请确保已安装所有依赖: pip install customtkinter")
            sys.exit(1)

if __name__ == "__main__":
    main()
