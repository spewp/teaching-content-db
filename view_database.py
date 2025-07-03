#!/usr/bin/env python3
"""
Database Content Viewer - Simple command-line tool to view teaching content
"""

import sys
from pathlib import Path

# Add backend directory to Python path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

def main():
    try:
        from database.database import get_database_manager
        from database.models import Content, Tag, Category
        
        # Get database manager
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        print("🎓 Teaching Content Database Viewer")
        print("=" * 50)
        
        # Show statistics
        content_count = session.query(Content).count()
        tag_count = session.query(Tag).count()
        category_count = session.query(Category).count()
        
        print(f"📊 Database Statistics:")
        print(f"   📄 Content Items: {content_count}")
        print(f"   🏷️  Tags: {tag_count}")
        print(f"   📁 Categories: {category_count}")
        
        if content_count > 0:
            print(f"\n📋 All Content:")
            content_list = session.query(Content).order_by(Content.date_created.desc()).all()
            
            for i, content in enumerate(content_list, 1):
                # Get tags
                tag_names = [tag.name for tag in content.tags] if content.tags else []
                tag_str = f" [{', '.join(tag_names)}]" if tag_names else ""
                
                print(f"{i:2d}. 📄 {content.title}{tag_str}")
                print(f"     Subject: {content.subject or 'N/A'} | Grade: {content.grade_level or 'N/A'}")
                if content.description:
                    desc = content.description[:100] + "..." if len(content.description) > 100 else content.description
                    print(f"     {desc}")
                print(f"     Created: {content.date_created.strftime('%Y-%m-%d') if content.date_created else 'N/A'}")
                print()
        
        else:
            print("\n📝 No content found in database. You can:")
            print("   1. Run the web interface to add content")
            print("   2. Use the init_database.py script to add sample data")
        
        session.close()
        
    except ImportError as e:
        print(f"❌ Error importing database modules: {e}")
        print("Make sure you're in the project directory and the database is set up.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 