#!/usr/bin/env python3
"""
Database Initialization Script for Teaching Content Database

This script creates the SQLite database, tables, and adds sample data.
Run this after setting up the Python environment.

Usage:
    python init_database.py
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

try:
    from database.database import init_db, get_database_manager
    print("✅ Successfully imported database modules")
except ImportError as e:
    print(f"❌ Failed to import database modules: {e}")
    print("Make sure you have installed the required dependencies:")
    print("  pip install Flask SQLAlchemy Flask-SQLAlchemy")
    sys.exit(1)

def main():
    """Main initialization function"""
    print("=" * 60)
    print("🚀 Teaching Content Database Initialization")
    print("=" * 60)
    
    # Get database manager
    try:
        db_manager = get_database_manager()
        print(f"📂 Database location: {db_manager.database_url}")
    except Exception as e:
        print(f"❌ Failed to create database manager: {e}")
        return False
    
    # Initialize database
    try:
        success = init_db()
        if success:
            print("=" * 60)
            print("🎉 Database initialization completed successfully!")
            print("=" * 60)
            
            # Display summary
            session = db_manager.get_session()
            try:
                from database.models import Content, Tag, Category
                
                content_count = session.query(Content).count()
                tag_count = session.query(Tag).count()
                category_count = session.query(Category).count()
                
                print(f"📊 Database Summary:")
                print(f"   • Content items: {content_count}")
                print(f"   • Tags: {tag_count}")
                print(f"   • Categories: {category_count}")
                print()
                print("🔍 You can now:")
                print("   • View the database with DB Browser for SQLite")
                print("   • Start the Flask application")
                print("   • Begin uploading your teaching content")
                
            except Exception as e:
                print(f"⚠️ Could not retrieve database summary: {e}")
            finally:
                session.close()
                
            return True
        else:
            print("💥 Database initialization failed!")
            return False
            
    except Exception as e:
        print(f"❌ Unexpected error during initialization: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 