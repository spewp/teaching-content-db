#!/usr/bin/env python3
"""
Setup validation script for Teaching Content Database
This script checks if all requirements are met to run the launcher successfully.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is adequate"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python version is adequate (3.8+)")
        return True
    else:
        print("❌ Python version is too old. Please upgrade to Python 3.8+")
        return False

def check_project_files():
    """Check if required project files exist"""
    required_files = [
        'start_server.py',
        'simple_launcher.py',
        'requirements.txt',
        'backend/database/database.py',
        'frontend/index.html'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✅ Found: {file_path}")
    
    if missing_files:
        print("\n❌ Missing required files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    else:
        print("✅ All required project files found")
        return True

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'flask',
        'sqlalchemy',
        'flask_cors',
        'werkzeug'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is not installed")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required dependencies are installed")
        return True

def check_database():
    """Check if database file exists"""
    db_path = Path('teaching_content.db')
    if db_path.exists():
        print(f"✅ Database file found: {db_path}")
        print(f"  Size: {db_path.stat().st_size / 1024:.1f} KB")
        return True
    else:
        print("❌ Database file not found")
        print("  Run: python init_database.py")
        return False

def main():
    """Main validation function"""
    print("🔍 Teaching Content Database - Setup Validation")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Project Files", check_project_files),
        ("Dependencies", check_dependencies),
        ("Database", check_database)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        result = check_func()
        results.append((name, result))
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} checks passed")
    
    if passed == len(results):
        print("\n🎉 All checks passed! You can run the launcher:")
        print("   python simple_launcher.py")
    elif passed >= 3:
        print("\n⚠️ Most checks passed. The launcher might work but may have issues.")
        print("   Try running: python simple_launcher.py")
    else:
        print("\n❌ Several issues found. Please fix them before running the launcher.")
    
    print("\n💡 LAUNCHER USAGE:")
    print("1. Run: python simple_launcher.py")
    print("2. Click 'Check Setup' to verify configuration")
    print("3. Click 'Start Server' to launch the web application")
    print("4. Click 'Stop Server' to properly shut down the server")
    print("5. Click 'Open in Browser' to access the web interface")
    print("6. The URL will be: http://127.0.0.1:5000")

if __name__ == "__main__":
    main() 