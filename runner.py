"""
Simple runner script for the automated lo-fi YouTube channel generator
Run this after installing dependencies with: pip install -r requirements.txt
"""
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Import and run main
from main import main

if __name__ == "__main__":
    main()

