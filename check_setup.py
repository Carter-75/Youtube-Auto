"""
Setup verification script - checks if all dependencies and APIs are ready
Run this before running the main automation

WINDOWS ONLY - This project is designed for Windows operating systems
"""
import sys
import subprocess
import platform
from pathlib import Path


def check_windows():
    """Check if running on Windows"""
    if platform.system() == "Windows":
        print(f"[OK] Windows detected: {platform.version()}")
        return True
    else:
        print(f"[ERROR] This project requires Windows (detected: {platform.system()})")
        return False


def check_python_version():
    """Check if Python version is 3.11+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print("[OK] Python version:", f"{version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"[ERROR] Python 3.11+ required, you have {version.major}.{version.minor}.{version.micro}")
        return False


def check_dependencies():
    """Check if all Python packages are installed"""
    required = [
        'dotenv',
        'requests',
        'openai',
        'google.auth',
        'googleapiclient',
        'PIL',
        'retry'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"[OK] {package}")
        except ImportError:
            print(f"[MISSING] {package}")
            missing.append(package)
    
    if missing:
        print("\n[WARNING] Install missing packages with: pip install -r requirements.txt")
        return False
    return True


def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"[OK] FFmpeg: {version_line}")
            return True
        else:
            print("[ERROR] FFmpeg: installed but not working properly")
            return False
    except FileNotFoundError:
        print("[ERROR] FFmpeg: not found")
        print("   Install: https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        print(f"[ERROR] FFmpeg: error checking - {e}")
        return False


def check_env_file():
    """Check if .env file exists and has keys"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("[ERROR] .env file not found")
        print("   Create one by copying env_template.txt")
        return False
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    required_keys = [
        'SUNO_API_KEY',
        'OPENAI_API_KEY',
        'YOUTUBE_CLIENT_ID',
        'YOUTUBE_CLIENT_SECRET'
    ]
    
    missing_keys = []
    placeholder_keys = []
    
    for key in required_keys:
        if key not in content:
            missing_keys.append(key)
        elif f'{key}=your_' in content or f'{key}=' in content and content.split(f'{key}=')[1].split('\n')[0].strip() == '':
            placeholder_keys.append(key)
    
    if missing_keys:
        print(f"[ERROR] .env file missing keys: {', '.join(missing_keys)}")
        return False
    
    if placeholder_keys:
        print(f"[WARNING] .env has placeholder values for: {', '.join(placeholder_keys)}")
        print("   Replace with your actual API keys")
        return False
    
    print("[OK] .env file configured")
    return True


def check_directories():
    """Check if required directories exist"""
    dirs = ['audio', 'thumbnails', 'metadata', 'src']
    all_exist = True
    
    for dir_name in dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"[OK] {dir_name}/ folder")
        else:
            print(f"[ERROR] {dir_name}/ folder missing")
            all_exist = False
    
    return all_exist


def main():
    print("=" * 60)
    print("Setup Verification for Lo-Fi Automation")
    print("WINDOWS ONLY PROJECT")
    print("=" * 60)
    print()
    
    checks = [
        ("Windows OS", check_windows),
        ("Python Version", check_python_version),
        ("Python Dependencies", check_dependencies),
        ("FFmpeg", check_ffmpeg),
        ("Environment Variables", check_env_file),
        ("Directory Structure", check_directories)
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        result = check_func()
        results.append(result)
    
    print("\n" + "=" * 60)
    
    if all(results):
        print("[SUCCESS] All checks passed! You're ready to run the automation.")
        print("   Run: python runner.py")
    else:
        print("[WARNING] Some checks failed. Fix the issues above before running.")
        print("   See README.md for help")
    
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

