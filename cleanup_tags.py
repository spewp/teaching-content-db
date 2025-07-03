"""
Script to clean up unwanted tags and ensure allowed tags exist
"""

import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Define allowed tags
ALLOWED_TAGS = [
    'worksheet', 'lesson-plan', 'assessment', 'interactive', 
    'homework', 'group-work', 'individual', 'beginner', 
    'advanced', 'resource', 'activity'
]

def cleanup_tags():
    """Clean up unwanted tags and ensure allowed tags exist"""
    conn = sqlite3.connect('teaching_content.db')
    cursor = conn.cursor()
    
    try:
        # First, get all existing tags
        cursor.execute('SELECT id, name FROM tags')
        all_tags = cursor.fetchall()
        
        logging.info("=== CURRENT TAGS ===")
        for tag_id, tag_name in all_tags:
            logging.info(f"  {tag_id}: {tag_name}")
        
        # Delete unwanted tags
        deleted_count = 0
        for tag_id, tag_name in all_tags:
            if tag_name not in ALLOWED_TAGS:
                # Check if tag is in use
                cursor.execute('SELECT COUNT(*) FROM content_tags WHERE tag_id = ?', (tag_id,))
                usage_count = cursor.fetchone()[0]
                
                if usage_count > 0:
                    logging.warning(f"⚠️  Tag '{tag_name}' (ID: {tag_id}) is used {usage_count} times - removing associations")
                    # Remove tag associations
                    cursor.execute('DELETE FROM content_tags WHERE tag_id = ?', (tag_id,))
                
                # Delete the tag
                cursor.execute('DELETE FROM tags WHERE id = ?', (tag_id,))
                logging.info(f"❌ Deleted tag: {tag_name} (ID: {tag_id})")
                deleted_count += 1
        
        # Ensure all allowed tags exist
        created_count = 0
        for tag_name in ALLOWED_TAGS:
            cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
            if not cursor.fetchone():
                # Create the tag
                cursor.execute(
                    'INSERT INTO tags (name, description, color) VALUES (?, ?, ?)',
                    (tag_name, f"Standard tag for {tag_name.replace('-', ' ')}", '')
                )
                logging.info(f"✅ Created tag: {tag_name}")
                created_count += 1
        
        # Commit changes
        conn.commit()
        
        logging.info(f"\n=== SUMMARY ===")
        logging.info(f"Deleted {deleted_count} unwanted tags")
        logging.info(f"Created {created_count} missing allowed tags")
        
        # Show final tag list
        cursor.execute('SELECT id, name FROM tags ORDER BY name')
        final_tags = cursor.fetchall()
        logging.info(f"\n=== FINAL TAGS ({len(final_tags)} total) ===")
        for tag_id, tag_name in final_tags:
            logging.info(f"  {tag_id}: {tag_name}")
        
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_tags()
    logging.info("\n✅ Tag cleanup completed!") 