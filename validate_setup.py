#!/usr/bin/env python3
"""
Simple validation script for Teaching Content Database setup

This script performs basic validation checks without requiring database creation.

Usage:
    python validate_setup.py
"""

import sys
import os
from pathlib import Path

def check_file_structure():
    """Check that all required files exist"""
    print("📁 Checking file structure...")
    
    required_files = [
        'config.py',
        'requirements.txt',
        'init_database.py',
        'backend/__init__.py',
        'backend/database/__init__.py',
        'backend/database/models.py',
        'backend/database/database.py',
        'README.md'
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            existing_files.append(file_path)
            print(f"   ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"   ❌ {file_path}")
    
    if missing_files:
        print(f"\n⚠️ Missing files: {len(missing_files)}")
        return False
    else:
        print(f"\n✅ All {len(existing_files)} required files found")
        return True

def check_python_dependencies():
    """Check if required Python packages are available"""
    print("\n🐍 Checking Python dependencies...")
    
    required_packages = [
        ('sqlalchemy', 'SQLAlchemy'),
        ('flask', 'Flask'),
        ('flask_sqlalchemy', 'Flask-SQLAlchemy')
    ]
    
    missing_packages = []
    available_packages = []
    
    for package_name, display_name in required_packages:
        try:
            __import__(package_name)
            available_packages.append(display_name)
            print(f"   ✅ {display_name}")
        except ImportError:
            missing_packages.append(display_name)
            print(f"   ❌ {display_name}")
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("   💡 Install with: pip install Flask SQLAlchemy Flask-SQLAlchemy")
        return False
    else:
        print(f"\n✅ All {len(available_packages)} required packages available")
        return True

def check_directory_structure():
    """Check that required directories exist"""
    print("\n📂 Checking directory structure...")
    
    required_dirs = [
        'backend',
        'backend/api',
        'backend/database',
        'backend/utils',
        'frontend',
        'frontend/css',
        'frontend/js',
        'uploads',
        'uploads/assessments',
        'uploads/lesson-plans',
        'uploads/resources',
        'uploads/worksheets',
        'backups',
        'docs'
    ]
    
    missing_dirs = []
    existing_dirs = []
    
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if full_path.exists() and full_path.is_dir():
            existing_dirs.append(dir_path)
            print(f"   ✅ {dir_path}/")
        else:
            missing_dirs.append(dir_path)
            print(f"   ❌ {dir_path}/")
    
    if missing_dirs:
        print(f"\n⚠️ Missing directories: {len(missing_dirs)}")
        return False
    else:
        print(f"\n✅ All {len(existing_dirs)} required directories found")
        return True

def check_config_file():
    """Check that config.py is properly configured"""
    print("\n⚙️ Checking configuration...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path.cwd()))
        
        import config
        
        # Check for required configuration classes
        required_configs = ['Config', 'DevelopmentConfig', 'ProductionConfig', 'TestingConfig']
        missing_configs = []
        
        for config_name in required_configs:
            if hasattr(config, config_name):
                print(f"   ✅ {config_name}")
            else:
                missing_configs.append(config_name)
                print(f"   ❌ {config_name}")
        
        # Check for config mapping
        if hasattr(config, 'config'):
            print("   ✅ config mapping")
        else:
            print("   ❌ config mapping")
            missing_configs.append('config mapping')
        
        if missing_configs:
            print(f"\n⚠️ Missing configurations: {', '.join(missing_configs)}")
            return False
        else:
            print(f"\n✅ Configuration file properly set up")
            return True
            
    except ImportError as e:
        print(f"   ❌ Failed to import config.py: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error checking config.py: {e}")
        return False

def check_sqlite_availability():
    """Check that SQLite is available in Python"""
    print("\n🗄️ Checking SQLite availability...")
    
    try:
        import sqlite3
        version = sqlite3.sqlite_version
        python_version = sqlite3.version
        print(f"   ✅ SQLite version: {version}")
        print(f"   ✅ Python sqlite3 module: {python_version}")
        return True
    except ImportError:
        print("   ❌ SQLite not available in Python")
        return False

def main():
    """Run all validation checks"""
    print("=" * 60)
    print("🔍 Teaching Content Database - Setup Validation")
    print("=" * 60)
    
    all_checks_passed = True
    
    # Run all checks
    checks = [
        ("File Structure", check_file_structure),
        ("Directory Structure", check_directory_structure),
        ("Configuration", check_config_file),
        ("SQLite", check_sqlite_availability),
        ("Python Dependencies", check_python_dependencies),
    ]
    
    for check_name, check_function in checks:
        try:
            if not check_function():
                all_checks_passed = False
        except Exception as e:
            print(f"   ❌ {check_name} check failed with error: {e}")
            all_checks_passed = False
    
    # Final results
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("🎉 ALL VALIDATION CHECKS PASSED!")
        print("\n✅ Your setup is ready for database initialization.")
        print("\n📋 Next steps:")
        print("   1. Run: python test_database.py")
        print("   2. Run: python init_database.py") 
        print("   3. Proceed with Step 2.2: Implement basic CRUD operations")
    else:
        print("❌ SOME VALIDATION CHECKS FAILED!")
        print("\n🔧 Please fix the issues above before proceeding.")
        print("\n💡 Common fixes:")
        print("   • Install dependencies: pip install Flask SQLAlchemy Flask-SQLAlchemy")
        print("   • Check file permissions")
        print("   • Verify directory structure")
    print("=" * 60)
    
    return all_checks_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 