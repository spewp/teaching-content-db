"""
Database initialization and configuration for Teaching Content Database
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path

from .models import Base, Content, Tag, Category, ContentVersion

# Import migration functionality
try:
    from .migrations import DatabaseMigration
    MIGRATIONS_AVAILABLE = True
except ImportError:
    MIGRATIONS_AVAILABLE = False
    print("⚠️ Migration module not available")

class DatabaseManager:
    """Manages database connection and operations"""
    
    def __init__(self, database_url=None):
        """Initialize database manager with connection URL"""
        if database_url is None:
            # Use config from parent directory
            project_root = Path(__file__).parent.parent.parent
            database_path = project_root / 'teaching_content.db'
            database_url = f'sqlite:///{database_path}'
        
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            connect_args={'check_same_thread': False}  # SQLite specific
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("✅ Database tables created successfully")
            return True
        except SQLAlchemyError as e:
            print(f"❌ Error creating tables: {e}")
            return False
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            print("⚠️ All database tables dropped")
            return True
        except SQLAlchemyError as e:
            print(f"❌ Error dropping tables: {e}")
            return False
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    def init_database(self, with_sample_data=False):
        """Initialize database with tables and optional sample data"""
        print("🚀 Initializing Teaching Content Database...")
        
        # Create tables
        if not self.create_tables():
            return False
        
        # Run auto-categorization migrations if available (Step 1.2)
        if MIGRATIONS_AVAILABLE:
            print("🔄 Checking for required migrations...")
            migration = DatabaseMigration(self.database_url.replace('sqlite:///', ''))
            if not migration.add_auto_categorization_columns():
                print("⚠️ Migration failed, but basic tables created successfully")
        else:
            print("⚠️ Migration module not available, skipping auto-categorization setup")
        
        # Add sample data if requested (now defaults to False for production)
        if with_sample_data:
            if not self.add_sample_data():
                print("⚠️ Failed to add sample data, but tables created successfully")
        else:
            # Add only essential categories without test content
            self.add_essential_structure()
        
        print("✅ Database initialization complete!")
        return True
    
    def add_sample_data(self):
        """Add sample data for testing and development"""
        try:
            session = self.get_session()
            
            # Check if data already exists
            if session.query(Category).count() > 0:
                print("📊 Sample data already exists, skipping...")
                session.close()
                return True
            
            print("📊 Adding sample data...")
            
            # Create sample categories
            categories = [
                Category(name="English", description="English language, literature, reading, and writing"),
                Category(name="Religious Education", description="Religious studies, ethics, and spiritual education"),
                Category(name="Learning Support", description="Educational support, special needs, and learning assistance"),
                Category(name="Other", description="General content and miscellaneous educational materials"),
            ]
            
            session.add_all(categories)
            session.commit()
            
            # Create sample tags
            tags = [
                Tag(name="worksheet", description="Practice worksheets", color="#4CAF50"),
                Tag(name="lesson-plan", description="Teaching lesson plans", color="#2196F3"),
                Tag(name="assessment", description="Tests and quizzes", color="#FF9800"),
                Tag(name="interactive", description="Interactive activities", color="#9C27B0"),
                Tag(name="homework", description="Take-home assignments", color="#795548"),
                Tag(name="group-work", description="Collaborative activities", color="#009688"),
                Tag(name="individual", description="Individual work", color="#607D8B"),
                Tag(name="beginner", description="Beginner level", color="#8BC34A"),
                Tag(name="advanced", description="Advanced level", color="#F44336"),
            ]
            
            session.add_all(tags)
            session.commit()
            
            # Create sample content
            learning_support_category = next(cat for cat in categories if cat.name == "Learning Support")
            english_category = next(cat for cat in categories if cat.name == "English")
            other_category = next(cat for cat in categories if cat.name == "Other")
            worksheet_tag = next(tag for tag in tags if tag.name == "worksheet")
            lesson_tag = next(tag for tag in tags if tag.name == "lesson-plan")
            
            # Get content type tags for assignment
            assessment_tag = next(tag for tag in tags if tag.name == "assessment")
            
            sample_content = [
                Content(
                    title="Introduction to Fractions",
                    description="Basic worksheet covering fraction concepts for elementary students",
                    content_type="worksheet",  # Keep for now during transition
                    subject="Learning Support",
                    grade_level="3rd Grade",
                    difficulty_level="Easy",
                    duration=30,
                    file_path="web-content/introduction-to-fractions.pdf",
                    original_filename="fractions_intro.pdf",
                    mime_type="application/pdf",
                    file_size=245760,
                    keywords="fractions math elementary basic support",
                    category=learning_support_category,
                    tags=[worksheet_tag]
                ),
                Content(
                    title="Reading Comprehension Strategies",
                    description="Comprehensive lesson plan for teaching reading comprehension",
                    content_type="lesson-plan",  # Keep for now during transition
                    subject="English",
                    grade_level="5th Grade",
                    difficulty_level="Medium",
                    duration=60,
                    file_path="web-content/reading-comprehension-lesson.docx",
                    original_filename="reading_comprehension_lesson.docx",
                    mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    file_size=98304,
                    keywords="reading comprehension english literature",
                    category=english_category,
                    tags=[lesson_tag]
                ),
                Content(
                    title="General Knowledge Assessment",
                    description="Multiple choice test covering various educational topics",
                    content_type="assessment",  # Keep for now during transition
                    subject="Other",
                    grade_level="8th Grade",
                    difficulty_level="Medium",
                    duration=45,
                    file_path="web-content/general-knowledge-assessment.pdf",
                    original_filename="general_knowledge_test.pdf",
                    mime_type="application/pdf",
                    file_size=156672,
                    keywords="general knowledge assessment test various topics",
                    category=other_category,
                    tags=[assessment_tag]
                )
            ]
            
            session.add_all(sample_content)
            session.commit()
            
            print("✅ Sample data added successfully")
            session.close()
            return True
            
        except SQLAlchemyError as e:
            print(f"❌ Error adding sample data: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return False
    
    def add_essential_structure(self):
        """Add only essential categories and basic tags without test content"""
        try:
            session = self.get_session()
            
            # Check if structure already exists
            if session.query(Category).count() > 0:
                print("📊 Essential structure already exists, skipping...")
                session.close()
                return True
            
            print("📊 Adding essential structure...")
            
            # Create essential categories (subjects)
            categories = [
                Category(name="English", description="Reading, writing, literature"),
                Category(name="Religious Education", description="Religious studies, ethics, and spiritual education"),
                Category(name="Learning Support", description="Educational support, special needs, and learning assistance"),
                Category(name="Other", description="General content and miscellaneous educational materials"),
            ]
            
            session.add_all(categories)
            
            # Create essential organizational tags (without test colors/descriptions)
            essential_tags = [
                Tag(name="worksheet", description="Practice worksheets", color="#4CAF50"),
                Tag(name="lesson-plan", description="Teaching lesson plans", color="#2196F3"),
                Tag(name="assessment", description="Tests and quizzes", color="#FF9800"),
                Tag(name="resource", description="Educational resources", color="#9C27B0"),
                Tag(name="activity", description="Learning activities", color="#009688"),
            ]
            
            session.add_all(essential_tags)
            session.commit()
            
            print("✅ Essential structure added successfully")
            session.close()
            return True
            
        except SQLAlchemyError as e:
            print(f"❌ Error adding essential structure: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return False

# Global database manager instance
db_manager = None

def get_database_manager():
    """Get or create the global database manager"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def init_db():
    """Initialize the database (convenience function)"""
    manager = get_database_manager()
    return manager.init_database()

if __name__ == "__main__":
    # Run database initialization if script is executed directly
    print("🔧 Running database initialization...")
    if init_db():
        print("🎉 Database setup complete!")
    else:
        print("💥 Database setup failed!") 