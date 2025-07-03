"""
Database migration utilities for Teaching Content Database

Handles safe schema upgrades and data integrity during database evolution.
"""

import sqlite3
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigration:
    """Handles database schema migrations"""
    
    def __init__(self, database_path=None):
        if database_path is None:
            # Use default database path
            project_root = Path(__file__).parent.parent.parent
            database_path = project_root / 'teaching_content.db'
        
        self.database_path = database_path
        self.database_url = f'sqlite:///{database_path}'
        
    def check_column_exists(self, table_name, column_name):
        """Check if a column exists in a table"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                return column_name in columns
        except sqlite3.Error as e:
            logger.error(f"Error checking column existence: {e}")
            return False
    
    def check_index_exists(self, index_name):
        """Check if an index exists"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking index existence: {e}")
            return False
    
    def add_auto_categorization_columns(self):
        """Add auto-categorization columns to content table (Step 1.2)"""
        logger.info("🔄 Starting auto-categorization schema migration...")
        
        try:
            engine = create_engine(self.database_url)
            
            with engine.connect() as connection:
                # Check if columns already exist
                columns_to_add = [
                    ('auto_categorized', 'BOOLEAN DEFAULT FALSE'),
                    ('categorization_confidence', 'REAL'),  # SQLite uses REAL for floating point
                    ('suggested_tags', 'TEXT')
                ]
                
                columns_added = []
                
                for column_name, column_def in columns_to_add:
                    if not self.check_column_exists('content', column_name):
                        try:
                            sql = f"ALTER TABLE content ADD COLUMN {column_name} {column_def}"
                            connection.execute(text(sql))
                            columns_added.append(column_name)
                            logger.info(f"✅ Added column: {column_name}")
                        except SQLAlchemyError as e:
                            logger.error(f"❌ Failed to add column {column_name}: {e}")
                            raise
                    else:
                        logger.info(f"⚠️ Column {column_name} already exists, skipping")
                
                # Add performance indexes
                indexes_to_create = [
                    ('idx_content_auto_categorized', 'content', 'auto_categorized'),
                    ('idx_content_confidence', 'content', 'categorization_confidence')
                ]
                
                indexes_added = []
                
                for index_name, table_name, column_name in indexes_to_create:
                    if not self.check_index_exists(index_name):
                        try:
                            sql = f"CREATE INDEX {index_name} ON {table_name}({column_name})"
                            connection.execute(text(sql))
                            indexes_added.append(index_name)
                            logger.info(f"✅ Created index: {index_name}")
                        except SQLAlchemyError as e:
                            logger.error(f"❌ Failed to create index {index_name}: {e}")
                            raise
                    else:
                        logger.info(f"⚠️ Index {index_name} already exists, skipping")
                
                connection.commit()
                
                # Summary
                if columns_added or indexes_added:
                    logger.info("🎉 Auto-categorization migration completed successfully!")
                    if columns_added:
                        logger.info(f"   📊 Columns added: {', '.join(columns_added)}")
                    if indexes_added:
                        logger.info(f"   🔍 Indexes created: {', '.join(indexes_added)}")
                else:
                    logger.info("✅ Database already up to date with auto-categorization schema")
                
                return True
                
        except Exception as e:
            logger.error(f"💥 Migration failed: {e}")
            return False
    
    def verify_migration(self):
        """Verify that the migration was successful"""
        logger.info("🔍 Verifying migration...")
        
        required_columns = ['auto_categorized', 'categorization_confidence', 'suggested_tags']
        required_indexes = ['idx_content_auto_categorized', 'idx_content_confidence']
        
        # Check columns
        missing_columns = []
        for column in required_columns:
            if not self.check_column_exists('content', column):
                missing_columns.append(column)
        
        # Check indexes
        missing_indexes = []
        for index in required_indexes:
            if not self.check_index_exists(index):
                missing_indexes.append(index)
        
        if missing_columns or missing_indexes:
            logger.error("❌ Migration verification failed!")
            if missing_columns:
                logger.error(f"   Missing columns: {', '.join(missing_columns)}")
            if missing_indexes:
                logger.error(f"   Missing indexes: {', '.join(missing_indexes)}")
            return False
        else:
            logger.info("✅ Migration verification successful!")
            return True

def run_auto_categorization_migration():
    """Convenience function to run the auto-categorization migration"""
    migration = DatabaseMigration()
    
    logger.info("=" * 60)
    logger.info("🚀 MCP Smart Notes Integration - Step 1.2 Migration")
    logger.info("=" * 60)
    
    # Run migration
    if migration.add_auto_categorization_columns():
        # Verify migration
        if migration.verify_migration():
            logger.info("🎉 Step 1.2 migration completed successfully!")
            return True
        else:
            logger.error("💥 Migration verification failed!")
            return False
    else:
        logger.error("💥 Migration failed!")
        return False

if __name__ == "__main__":
    # Run migration if script is executed directly
    success = run_auto_categorization_migration()
    exit(0 if success else 1)

def add_auto_processing_columns(database_path=None):
    """Add Task 2.2 auto-processing tracking columns"""
    migration = DatabaseMigration(database_path)
    logger.info("🔄 Starting Task 2.2 auto-processing schema migration...")
    
    try:
        engine = create_engine(migration.database_url)
        
        with engine.connect() as connection:
            # Check if columns already exist
            columns_to_add = [
                ('auto_processed', 'BOOLEAN DEFAULT FALSE'),
                ('generated_metadata', 'TEXT')  # JSON of what was auto-generated
            ]
            
            columns_added = []
            
            for column_name, column_def in columns_to_add:
                if not migration.check_column_exists('content', column_name):
                    try:
                        sql = f"ALTER TABLE content ADD COLUMN {column_name} {column_def}"
                        connection.execute(text(sql))
                        columns_added.append(column_name)
                        logger.info(f"✅ Added column: {column_name}")
                    except SQLAlchemyError as e:
                        logger.error(f"❌ Failed to add column {column_name}: {e}")
                        raise
                else:
                    logger.info(f"⚠️ Column {column_name} already exists, skipping")
            
            connection.commit()
            
            if columns_added:
                logger.info("🎉 Task 2.2 auto-processing migration completed successfully!")
                logger.info(f"   📊 Columns added: {', '.join(columns_added)}")
            else:
                logger.info("✅ Database already has auto-processing columns")
            
            return True
            
    except Exception as e:
        logger.error(f"💥 Migration failed: {e}")
        return False 