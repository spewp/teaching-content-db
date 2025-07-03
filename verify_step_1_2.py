#!/usr/bin/env python3
"""
Verification Script for Step 1.2: Auto-Categorization Schema

This script checks if the auto-categorization schema enhancements have been
properly applied to the database.

Usage:
    python verify_step_1_2.py
"""

import sys
import sqlite3
from pathlib import Path

def check_database_schema():
    """Check if the Step 1.2 schema changes are present"""
    
    # Find the database
    project_root = Path(__file__).parent
    database_path = project_root / 'teaching_content.db'
    
    if not database_path.exists():
        print("❌ Database file not found!")
        print(f"   Expected location: {database_path}")
        print("   Run 'python init_database.py' first to create the database.")
        return False
    
    print(f"🔍 Checking database schema at: {database_path}")
    print("=" * 60)
    
    try:
        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()
            
            # Check content table structure
            cursor.execute("PRAGMA table_info(content)")
            columns = cursor.fetchall()
            
            print("📊 Content table columns:")
            column_names = []
            for col in columns:
                col_id, name, data_type, not_null, default_val, primary_key = col
                column_names.append(name)
                print(f"   • {name} ({data_type})")
            
            print("\n🔍 Checking for Step 1.2 enhancements...")
            
            # Check for required columns
            required_columns = [
                'auto_categorized',
                'categorization_confidence', 
                'suggested_tags'
            ]
            
            missing_columns = []
            found_columns = []
            
            for req_col in required_columns:
                if req_col in column_names:
                    found_columns.append(req_col)
                    print(f"   ✅ {req_col} - Found")
                else:
                    missing_columns.append(req_col)
                    print(f"   ❌ {req_col} - Missing")
            
            # Check for indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
            
            print("\n🔍 Checking for performance indexes...")
            required_indexes = [
                'idx_content_auto_categorized',
                'idx_content_confidence'
            ]
            
            missing_indexes = []
            found_indexes = []
            
            for req_idx in required_indexes:
                if req_idx in indexes:
                    found_indexes.append(req_idx)
                    print(f"   ✅ {req_idx} - Found")
                else:
                    missing_indexes.append(req_idx)
                    print(f"   ❌ {req_idx} - Missing")
            
            # Summary
            print("\n" + "=" * 60)
            
            if not missing_columns and not missing_indexes:
                print("🎉 Step 1.2 Migration Status: COMPLETE")
                print("✅ All auto-categorization enhancements are in place!")
                print("\n📋 Ready for:")
                print("   • Step 1.3: Frontend Suggestion Interface")
                print("   • Content Analysis API integration")
                print("   • Intelligent auto-categorization")
                return True
            else:
                print("⚠️ Step 1.2 Migration Status: INCOMPLETE")
                if missing_columns:
                    print(f"❌ Missing columns: {', '.join(missing_columns)}")
                if missing_indexes:
                    print(f"❌ Missing indexes: {', '.join(missing_indexes)}")
                print("\n🔧 Action Required:")
                print("   Run: python run_migration_step_1_2.py")
                return False
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main verification function"""
    print("=" * 60)
    print("🔍 Step 1.2 Schema Verification")
    print("   Auto-Categorization Enhancements Check")
    print("=" * 60)
    
    success = check_database_schema()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 