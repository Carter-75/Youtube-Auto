"""
Simple runner script for the automated lo-fi YouTube channel generator
Run this after installing dependencies with: pip install -r requirements.txt

WINDOWS ONLY - This project is designed for Windows operating systems
"""
import sys
import platform
from pathlib import Path

# Check if running on Windows
if platform.system() != "Windows":
    print("=" * 60)
    print("ERROR: This project only supports Windows")
    print(f"Detected OS: {platform.system()}")
    print("=" * 60)
    sys.exit(1)

# Add src directory to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Import and run main
from main import main

if __name__ == "__main__":
    main()

