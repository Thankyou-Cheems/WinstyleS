"""
Build script for WinstyleS
Creates a standalone executable using PyInstaller.

Usage:
    python build.py

The output will be in the 'dist' folder.
"""

import os
import subprocess
import sys


def main():
    print("=" * 50)
    print("WinstyleS Build Script")
    print("=" * 50)
    print()

    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed")

    # Get project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    spec_file = os.path.join(project_root, "winstyles.spec")

    if not os.path.exists(spec_file):
        print(f"✗ Spec file not found: {spec_file}")
        sys.exit(1)

    print(f"✓ Using spec file: {spec_file}")
    print()
    print("Building executable...")
    print("-" * 50)

    # Run PyInstaller
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", spec_file],
        cwd=project_root
    )

    if result.returncode == 0:
        print()
        print("=" * 50)
        print("✓ Build successful!")
        print()
        print(f"Executable: {os.path.join(project_root, 'dist', 'WinstyleS.exe')}")
        print("=" * 50)
    else:
        print()
        print("=" * 50)
        print("✗ Build failed!")
        print("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()
