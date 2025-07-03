"""
Database models for Teaching Content Database
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Association table for many-to-many relationship between Content and Tags
content_tags = Table('content_tags', Base.metadata,
    Column('content_id', Integer, ForeignKey('content.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Content(Base):
    """Main content table storing all teaching materials"""
    __tablename__ = 'content'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Basic content information
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    content = Column(Text)  # Store actual content text for web-based content
    content_type = Column(String(50), nullable=True, index=True)  # lesson-plan, worksheet, assessment, resource (transitioning to tags)
    subject = Column(String(100), index=True)  # Math, Science, English, etc.
    
    # File information
    original_filename = Column(String(255))
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # in bytes
    mime_type = Column(String(100))
    
    # Academic metadata
    grade_level = Column(String(50))  # K-12, College, etc.
    difficulty_level = Column(String(20))  # Easy, Medium, Hard
    duration = Column(Integer)  # estimated time in minutes
    
    # Status and workflow
    status = Column(String(20), default='active')  # active, archived, draft
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    date_uploaded = Column(DateTime, default=datetime.utcnow)
    
    # Search and organization
    keywords = Column(Text)  # space-separated keywords for search
    
    # Auto-categorization tracking (MCP Smart Notes Integration)
    auto_categorized = Column(Boolean, default=False, index=True)
    categorization_confidence = Column(Float)  # Using Float instead of DECIMAL for SQLite compatibility
    suggested_tags = Column(Text)  # JSON array of AI-suggested tags
    
    # Auto-processing tracking (Task 2.2)
    auto_processed = Column(Boolean, default=False)
    generated_metadata = Column(Text)  # JSON of what was auto-generated
    
    # Foreign keys
    category_id = Column(Integer, ForeignKey('categories.id'))
    
    # Relationships
    category = relationship("Category", back_populates="content_items")
    tags = relationship("Tag", secondary=content_tags, back_populates="content_items")
    
    def __repr__(self):
        return f"<Content(id={self.id}, title='{self.title}', type='{self.content_type}')>"

class Tag(Base):
    """Tags for flexible content organization"""
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    color = Column(String(7))  # hex color code for UI
    
    # Metadata
    date_created = Column(DateTime, default=datetime.utcnow)
    usage_count = Column(Integer, default=0)  # track how often tag is used
    
    # Relationships
    content_items = relationship("Content", secondary=content_tags, back_populates="tags")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"

class Category(Base):
    """Hierarchical categories for content organization"""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    
    # Hierarchical structure
    parent_id = Column(Integer, ForeignKey('categories.id'))
    sort_order = Column(Integer, default=0)
    
    # Metadata
    date_created = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
    content_items = relationship("Content", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

class ContentVersion(Base):
    """Version history for content items (future feature)"""
    __tablename__ = 'content_versions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('content.id'), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    
    # Change tracking
    change_description = Column(Text)
    date_created = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer)
    
    # Relationships
    content = relationship("Content")
    
    def __repr__(self):
        return f"<ContentVersion(content_id={self.content_id}, version={self.version_number})>" 