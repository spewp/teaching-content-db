# Configuration settings for Teaching Content Database

import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    DATABASE_PATH = BASE_DIR / 'teaching_content.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
        'ppt', 'pptx', 'xls', 'xlsx', 'zip', 'mp4', 'mp3', 'wav'
    }
    
    # Content directories
    CONTENT_DIRS = {
        'assessments': UPLOAD_FOLDER / 'assessments',
        'lesson-plans': UPLOAD_FOLDER / 'lesson-plans', 
        'resources': UPLOAD_FOLDER / 'resources',
        'worksheets': UPLOAD_FOLDER / 'worksheets'
    }
    
    # Backup settings
    BACKUP_FOLDER = BASE_DIR / 'backups'
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_PATH = BASE_DIR / 'test_teaching_content.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
