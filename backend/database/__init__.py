"""
Database package for Teaching Content Database
"""

from .models import Base, Content, Tag, Category, ContentVersion
from .database import DatabaseManager, get_database_manager, init_db

__all__ = [
    'Base', 
    'Content', 
    'Tag', 
    'Category', 
    'ContentVersion',
    'DatabaseManager',
    'get_database_manager',
    'init_db'
] 