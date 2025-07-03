"""
Simple server startup script - Direct SQLAlchemy implementation
"""

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from pathlib import Path
import sys
import os
import hashlib
import uuid
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from sqlalchemy import func
import json

# Add backend to path for imports
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

# Import content analysis module (Task 1.1) at module level
try:
    from services.content_analyzer import ContentAnalyzer
    # Initialize ContentAnalyzer at module level for reuse
    content_analyzer = ContentAnalyzer()
    CONTENT_ANALYSIS_AVAILABLE = True
    logging.info(f"✅ Content analyzer initialized. LLM connected: {content_analyzer.client is not None}")
except ImportError as e:
    logging.error(f"Content analysis import failed: {e}")
    import traceback
    traceback.print_exc()
    CONTENT_ANALYSIS_AVAILABLE = False
    content_analyzer = None
except Exception as e:
    logging.error(f"Content analyzer initialization failed: {e}")
    import traceback
    traceback.print_exc()
    CONTENT_ANALYSIS_AVAILABLE = False
    content_analyzer = None

def create_simple_app():
    """Create Flask app with minimal configuration"""
    
    app = Flask(__name__)
    
    # Simple configuration
    app.config.update({
        'SECRET_KEY': 'dev-secret-key-for-testing',
        'DEBUG': True,
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max file size
        'UPLOAD_FOLDER': str(Path(__file__).parent / 'uploads')
    })
    
    # Import database components
    from database.database import get_database_manager
    from database.models import Content, Tag, Category, content_tags  # association table
    
    # Frontend directory path
    frontend_dir = Path(__file__).parent / 'frontend'
    
    # Enable CORS
    CORS(app, origins=['*'])
    
    # File upload configuration
    ALLOWED_EXTENSIONS = {
        'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt',  # Documents
        'ppt', 'pptx', 'odp',  # Presentations
        'xls', 'xlsx', 'ods', 'csv',  # Spreadsheets
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg',  # Images
        'mp3', 'wav', 'ogg', 'm4a',  # Audio
        'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm',  # Video
        'zip', 'rar', '7z', 'tar', 'gz'  # Archives
    }
    
    CONTENT_TYPE_MAPPING = {
        'lesson-plan': 'lesson-plans',
        'lesson-plans': 'lesson-plans',
        'worksheet': 'worksheets',
        'worksheets': 'worksheets',
        'assessment': 'assessments',
        'assessments': 'assessments',
        'resource': 'resources',
        'resources': 'resources'
    }
    
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    def sanitize_filename(filename):
        """Sanitize filename to prevent directory traversal and other security issues"""
        if not filename:
            return 'unnamed_file'
        
        # Use werkzeug's secure_filename for basic sanitization
        filename = secure_filename(filename)
        
        # Additional sanitization
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Ensure filename is not empty after sanitization
        if not filename or filename == '.':
            filename = 'unnamed_file'
            
        return filename
    
    def generate_unique_filename(original_filename, content_type=None):
        """Generate a unique filename while preserving the original extension"""
        if not original_filename:
            original_filename = 'file'
            
        # Extract extension
        if '.' in original_filename:
            name, ext = original_filename.rsplit('.', 1)
            ext = '.' + ext.lower()
        else:
            name = original_filename
            ext = ''
        
        # Generate unique identifier
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create unique filename
        unique_filename = f"{sanitize_filename(name)}_{timestamp}_{unique_id}{ext}"
        
        return unique_filename
    
    def get_file_hash(file_path):
        """Calculate SHA-256 hash of a file for duplicate detection"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logging.error(f"Error calculating file hash: {e}")
            return None
    
    def ensure_upload_directory(content_type):
        """Ensure the upload directory exists for the given content type"""
        # Map content type to directory name
        dir_name = CONTENT_TYPE_MAPPING.get(content_type, 'resources')
        
        upload_dir = Path(app.config['UPLOAD_FOLDER']) / dir_name
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        return str(upload_dir)
    
    def ensure_temp_directory():
        """Ensure temp directory exists for temporary file operations"""
        temp_dir = Path(app.config['UPLOAD_FOLDER']) / 'temp'
        temp_dir.mkdir(parents=True, exist_ok=True)
        return str(temp_dir)
    
    def cleanup_orphaned_files():
        """Clean up orphaned files that exist on disk but not in database - Task 3.3"""
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Get all file paths from database
            db_files = set()
            content_list = session.query(Content).filter(Content.file_path.isnot(None)).all()
            for content in content_list:
                db_files.add(content.file_path)
            
            session.close()
            
            # Scan upload directories for actual files
            upload_base = Path(app.config['UPLOAD_FOLDER'])
            orphaned_files = []
            
            for subdir in ['assessments', 'lesson-plans', 'resources', 'worksheets']:
                subdir_path = upload_base / subdir
                if subdir_path.exists():
                    for file_path in subdir_path.rglob('*'):
                        if file_path.is_file():
                            relative_path = str(file_path.relative_to(upload_base))
                            if relative_path not in db_files:
                                orphaned_files.append(str(file_path))
            
            # Clean up temp directory
            temp_dir = upload_base / 'temp'
            if temp_dir.exists():
                for file_path in temp_dir.rglob('*'):
                    if file_path.is_file():
                        # Remove files older than 1 hour from temp directory
                        try:
                            file_age = datetime.now().timestamp() - file_path.stat().st_mtime
                            if file_age > 3600:  # 1 hour in seconds
                                os.remove(str(file_path))
                                logging.info(f"Cleaned up temp file: {file_path}")
                        except Exception as e:
                            logging.error(f"Error cleaning temp file {file_path}: {e}")
            
            return {
                'orphaned_files': orphaned_files,
                'temp_cleaned': True
            }
            
        except Exception as e:
            logging.error(f"Cleanup error: {e}")
            return {
                'orphaned_files': [],
                'temp_cleaned': False,
                'error': str(e)
            }
    
    # Add basic security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY' 
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    # Initialize upload directories and temp directory
    ensure_temp_directory()

    @app.route('/api/')
    def api_root():
        return jsonify({
            'message': 'Teaching Content Database API - Simple Mode',
            'status': 'running',
            'version': '1.0.0'
        })
    
    @app.route('/api/status')
    def api_status():
        return jsonify({
            'message': 'Teaching Content Database API - Simple Mode',
            'status': 'running',
            'version': '1.0.0'
        })
    
    @app.route('/api/health')
    def health():
        try:
            # Test database connection
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                content_count = session.query(Content).count()
                session.close()
                
                return jsonify({
                    'status': 'healthy',
                    'message': 'API is running',
                    'database': {
                        'status': 'connected',
                        'content_count': content_count
                    }
                })
            except Exception as e:
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'degraded',
                'message': f'Database error: {str(e)}'
            }), 503
    
    @app.route('/api/stats')
    def get_stats():
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                content_count = session.query(Content).count()
                tag_count = session.query(Tag).count()
                category_count = session.query(Category).count()
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'content': {
                        'total': content_count
                    },
                    'tags': {
                        'total': tag_count
                    },
                    'categories': {
                        'total': category_count
                    },
                    'system': {
                        'status': 'healthy',
                        'version': '1.0.0'
                    }
                })
            except Exception as e:
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e),
                'content': {'total': 0},
                'tags': {'total': 0},
                'categories': {'total': 0}
            }), 500

    @app.route('/api/content', methods=['GET'])
    def get_content():
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                # Enhanced filtering support
                subject_filter = request.args.get('subject')
                
                if subject_filter:
                    # Filter by subject name (Phase 2B: Subject-based filtering)
                    content_list = session.query(Content).filter(Content.subject == subject_filter).all()
                else:
                    content_list = session.query(Content).all()
                
                # Enhanced conversion to dict with tags and category
                content_data = []
                for content in content_list:
                    # Get tags for this content
                    tags = [{'id': tag.id, 'name': tag.name, 'color': tag.color} for tag in content.tags]
                    
                    # Get category if exists
                    category = None
                    if content.category:
                        category = {'id': content.category.id, 'name': content.category.name}
                    
                    content_data.append({
                        'id': content.id,
                        'title': content.title,
                        # 'content_type': content.content_type,  # Removed - use tags instead
                        'subject': content.subject,
                        'description': content.description,
                        'content': getattr(content, 'content', ''),
                        'grade_level': getattr(content, 'grade_level', ''),
                        'duration': getattr(content, 'duration', None),
                        'keywords': getattr(content, 'keywords', ''),
                        'status': getattr(content, 'status', 'active'),
                        'created_at': str(getattr(content, 'date_created', '')),
                        'updated_at': str(getattr(content, 'date_modified', '')),
                        'tags': tags,  # Primary categorization method
                        'category': category,
                        # Enhanced subject information for filtering
                        'category_id': content.category_id,  # Keep for backwards compatibility
                        'subject_name': content.subject,     # Primary subject field for filtering
                        # File metadata fields
                        'file_path': getattr(content, 'file_path', None),
                        'original_filename': getattr(content, 'original_filename', None),
                        'file_size': getattr(content, 'file_size', None),
                        'mime_type': getattr(content, 'mime_type', None)
                    })
                
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'data': content_data,
                    'count': len(content_data)
                })
            except Exception as e:
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/content/<int:content_id>', methods=['GET'])
    def get_content_by_id(content_id):
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                content = session.query(Content).filter(Content.id == content_id).first()
                
                if not content:
                    session.close()
                    return jsonify({
                        'status': 'error',
                        'message': 'Content not found'
                    }), 404
                
                # Get tags for this content
                tags = [{'id': tag.id, 'name': tag.name, 'color': tag.color} for tag in content.tags]
                
                # Get category if exists
                category = None
                if content.category:
                    category = {'id': content.category.id, 'name': content.category.name}
                
                content_data = {
                    'id': content.id,
                    'title': content.title,
                    # 'content_type': content.content_type,  # Removed - use tags instead
                    'subject': content.subject,
                    'description': content.description,
                    'content': getattr(content, 'content', ''),
                    'grade_level': getattr(content, 'grade_level', ''),
                    'duration': getattr(content, 'duration', None),
                    'keywords': getattr(content, 'keywords', ''),
                    'status': getattr(content, 'status', 'active'),
                    'created_at': str(getattr(content, 'date_created', '')),
                    'updated_at': str(getattr(content, 'date_modified', '')),
                    'tags': tags,  # Primary categorization method
                    'category': category,
                    # Enhanced subject information for filtering
                    'category_id': content.category_id,  # Keep for backwards compatibility
                    'subject_name': content.subject,     # Primary subject field for filtering
                    # File metadata fields
                    'file_path': getattr(content, 'file_path', None),
                    'original_filename': getattr(content, 'original_filename', None),
                    'file_size': getattr(content, 'file_size', None),
                    'mime_type': getattr(content, 'mime_type', None)
                }
                
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'data': content_data
                })
            except Exception as e:
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/content', methods=['POST'])
    def create_content():
        try:
            data = request.get_json()
            if not data or not data.get('title'):
                return jsonify({
                    'status': 'error',
                    'message': 'Title is required'
                }), 400
            
            # Validate subject against new categories
            valid_subjects = ['English', 'Religious Education', 'Learning Support', 'Other']
            subject = data.get('subject', '')
            if subject and subject not in valid_subjects:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid subject. Must be one of: {", ".join(valid_subjects)}'
                }), 400
            
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                # Auto-assign category based on subject
                category_id = data.get('category_id')
                if subject and not category_id:
                    category = session.query(Category).filter(Category.name == subject).first()
                    if category:
                        category_id = category.id
                
                # Create new content (content_type now optional)
                new_content = Content(
                    title=data.get('title'),
                    content_type=data.get('content_type'),  # Optional - will be NULL if not provided
                    subject=subject,
                    description=data.get('description', ''),
                    content=data.get('content', ''),
                    grade_level=data.get('grade_level', ''),
                    duration=data.get('duration'),
                    keywords=data.get('keywords', ''),
                    category_id=category_id,
                    file_path=data.get('file_path', f"web-content/{data.get('title', 'untitled').lower().replace(' ', '-')[:50]}.txt")
                )
                
                session.add(new_content)
                session.commit()
                
                result_data = {
                    'id': new_content.id,
                    'title': new_content.title,
                    # 'content_type': new_content.content_type  # Removed - use tags instead
                }
                
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Content created successfully',
                    'data': result_data
                }), 201
            except Exception as e:
                session.rollback()
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/content/analyze', methods=['POST'])
    def analyze_content():
        """Analyze uploaded content for intelligent categorization - Task 1.1"""
        try:
            if not CONTENT_ANALYSIS_AVAILABLE:
                return jsonify({
                    'status': 'error',
                    'message': 'Content analysis not available - missing dependencies'
                }), 503
            
            # Check if file is present in request
            if 'file' not in request.files:
                return jsonify({
                    'status': 'error',
                    'message': 'No file provided for analysis'
                }), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    'status': 'error',
                    'message': 'No file selected'
                }), 400
            
            # Validate file type
            if not allowed_file(file.filename):
                return jsonify({
                    'status': 'error',
                    'message': f'File type not supported for analysis. Supported types: {", ".join(ALLOWED_EXTENSIONS)}'
                }), 400
            
            # Extract metadata from form
            metadata = {
                'title': request.form.get('title', ''),
                'description': request.form.get('description', ''),
                'filename': file.filename or ''
            }
            
            # Perform content analysis
            result = content_analyzer.analyze_uploaded_content(file, metadata)
            
            # Reset file pointer for potential subsequent use
            file.seek(0)
            
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"Content analysis error: {e}")
            return jsonify({
                'status': 'error',
                'message': 'Content analysis failed',
                'details': str(e)
            }), 500

    @app.route('/api/content/upload', methods=['POST'])
    def upload_content():
        """Upload a file and create content record - Task 1.1"""
        try:
            # Check if file is present in request
            if 'file' not in request.files:
                return jsonify({
                    'status': 'error',
                    'message': 'No file provided'
                }), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    'status': 'error',
                    'message': 'No file selected'
                }), 400
            
            # Validate file
            if not allowed_file(file.filename):
                return jsonify({
                    'status': 'error',
                    'message': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
                }), 400
            
            # Get form data
            title = request.form.get('title')
            content_type = request.form.get('content_type', 'resource')
            subject = request.form.get('subject', '')
            description = request.form.get('description', '')
            grade_level = request.form.get('grade_level', '')
            duration = request.form.get('duration')
            keywords = request.form.get('keywords', '')
            
            # Validate required fields
            if not title:
                filename = file.filename or 'unnamed_file'
                title = filename.rsplit('.', 1)[0] if '.' in filename else filename
            
            # Validate subject
            valid_subjects = ['English', 'Religious Education', 'Learning Support', 'Other']
            if subject and subject not in valid_subjects:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid subject. Must be one of: {", ".join(valid_subjects)}'
                }), 400
            
            # Prepare file storage
            upload_dir = ensure_upload_directory(content_type)
            unique_filename = generate_unique_filename(file.filename, content_type)
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save file
            try:
                file.save(file_path)
            except Exception as e:
                logging.error(f"Error saving file: {e}")
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to save file'
                }), 500
            
            # Get file information
            file_size = os.path.getsize(file_path)
            file_hash = get_file_hash(file_path)
            
            # Check for duplicates (optional feature)
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                # Auto-assign category based on subject
                category_id = None
                if subject:
                    category = session.query(Category).filter(Category.name == subject).first()
                    if category:
                        category_id = category.id
                
                # Create relative path for database storage
                relative_path = os.path.relpath(file_path, app.config['UPLOAD_FOLDER'])
                
                # Create new content record
                new_content = Content(
                    title=title,
                    content_type=content_type,
                    subject=subject,
                    description=description,
                    grade_level=grade_level,
                    duration=int(duration) if duration and duration.isdigit() else None,
                    keywords=keywords,
                    category_id=category_id,
                    file_path=relative_path,
                    original_filename=file.filename,
                    file_size=file_size,
                    mime_type=file.content_type or 'application/octet-stream'
                )
                
                session.add(new_content)
                session.commit()
                
                # Prepare response data
                result_data = {
                    'id': new_content.id,
                    'title': new_content.title,
                    'content_type': new_content.content_type,
                    'file_path': new_content.file_path,
                    'original_filename': new_content.original_filename,
                    'file_size': new_content.file_size,
                    'mime_type': new_content.mime_type,
                    'upload_success': True
                }
                
                session.close()
                
                logging.info(f"File uploaded successfully: {file.filename} -> {unique_filename}")
                
                return jsonify({
                    'status': 'success',
                    'message': 'File uploaded and content created successfully',
                    'data': result_data
                }), 201
                
            except Exception as e:
                session.rollback()
                session.close()
                # Clean up file if database operation failed
                try:
                    os.remove(file_path)
                except:
                    pass
                raise e
                
        except RequestEntityTooLarge:
            return jsonify({
                'status': 'error',
                'message': f'File too large. Maximum size is {app.config["MAX_CONTENT_LENGTH"] // (1024*1024)}MB'
            }), 413
        except Exception as e:
            logging.error(f"Upload error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/content/auto-upload', methods=['POST'])
    def auto_upload_content():
        """
        Task 2.2: Auto-Upload System - Zero-Touch Content Processing
        Complete automation pipeline:
        1. File upload → content extraction
        2. Single LLM call generates ALL metadata 
        3. Direct save to database
        4. Return success + generated metadata
        """
        try:
            if not CONTENT_ANALYSIS_AVAILABLE:
                return jsonify({
                    'status': 'error',
                    'message': 'Auto-upload requires content analysis module - missing dependencies'
                }), 503
            
            # Check if file is present in request
            if 'file' not in request.files:
                return jsonify({
                    'status': 'error',
                    'message': 'No file provided for auto-upload'
                }), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    'status': 'error',
                    'message': 'No file selected'
                }), 400
            
            # Validate file
            if not allowed_file(file.filename):
                return jsonify({
                    'status': 'error',
                    'message': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
                }), 400
            
            # Generate unique filename and prepare storage
            content_type = 'resource'  # Default, will be overridden by LLM
            upload_dir = ensure_upload_directory(content_type)
            unique_filename = generate_unique_filename(file.filename, content_type)
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save file first
            try:
                file.save(file_path)
                file_size = os.path.getsize(file_path)
            except Exception as e:
                logging.error(f"Error saving file during auto-upload: {e}")
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to save uploaded file'
                }), 500
            
            # Reset file pointer for content analysis
            file.seek(0)
            
            # Debug logging
            logging.info(f"🔍 Auto-upload debug: file={file.filename}, saved to={file_path}")
            logging.info(f"🔍 Content analyzer available: {content_analyzer is not None}")
            if content_analyzer:
                logging.info(f"🔍 Content analyzer LLM connected: {content_analyzer.client is not None}")
            
            # Run auto-processing to generate all metadata
            try:
                processing_result = content_analyzer.auto_process_and_save(file, file_path)
                logging.info(f"🔍 Processing result status: {processing_result.get('status', 'unknown')}")
            except Exception as e:
                logging.error(f"❌ Auto-processing exception: {e}")
                import traceback
                traceback.print_exc()
                # Clean up file on failure
                try:
                    os.remove(file_path)
                except:
                    pass
                return jsonify({
                    'status': 'error',
                    'message': f'Auto-processing exception: {str(e)}'
                }), 500
            
            if processing_result['status'] != 'success':
                # Clean up file on failure
                try:
                    os.remove(file_path)
                except:
                    pass
                error_msg = processing_result.get('message', 'Auto-processing failed')
                logging.error(f"❌ Auto-processing failed: {error_msg}")
                return jsonify({
                    'status': 'error',
                    'message': error_msg
                }), 500
            
            # Extract auto-generated data
            auto_data = processing_result['auto_data']
            
            # If content type changed, move file to correct directory
            if auto_data['content_type'] != content_type:
                new_upload_dir = ensure_upload_directory(auto_data['content_type'])
                new_file_path = os.path.join(new_upload_dir, unique_filename)
                try:
                    os.rename(file_path, new_file_path)
                    file_path = new_file_path
                except Exception as e:
                    logging.warning(f"Failed to move file to {auto_data['content_type']} directory: {e}")
            
            # Create relative path for database storage
            relative_path = os.path.relpath(file_path, app.config['UPLOAD_FOLDER'])
            
            # Save to database
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                # Auto-assign category based on subject
                category_id = None
                if auto_data['subject']:
                    category = session.query(Category).filter(Category.name == auto_data['subject']).first()
                    if category:
                        category_id = category.id
                
                # Create new content record with all auto-generated data
                new_content = Content(
                    title=auto_data['title'],
                    content_type=auto_data['content_type'],
                    subject=auto_data['subject'],
                    description=auto_data['description'],
                    content=auto_data.get('content', ''),
                    grade_level=auto_data['grade_level'],
                    difficulty_level=auto_data['difficulty_level'],
                    duration=auto_data['duration'],
                    keywords=auto_data['keywords'],
                    category_id=category_id,
                    file_path=relative_path,
                    original_filename=file.filename,
                    file_size=file_size,
                    mime_type=auto_data['mime_type'],
                    auto_categorized=True,
                    categorization_confidence=auto_data['categorization_confidence'],
                    suggested_tags=json.dumps(auto_data['suggested_tags']),
                    auto_processed=True,
                    generated_metadata=auto_data.get('generated_metadata', '{}')
                )
                
                session.add(new_content)
                session.flush()  # Get the ID
                
                # Auto-assign suggested tags - ONLY if they already exist
                if auto_data['suggested_tags']:
                    # Define allowed tags
                    ALLOWED_TAGS = ['worksheet', 'lesson-plan', 'assessment', 'interactive', 
                                   'homework', 'group-work', 'individual', 'beginner', 
                                   'advanced', 'resource', 'activity']
                    
                    for tag_name in auto_data['suggested_tags']:
                        # Only process if tag is in allowed list
                        if tag_name in ALLOWED_TAGS:
                            # Find existing tag (don't create new ones)
                            tag = session.query(Tag).filter(Tag.name == tag_name).first()
                            if tag:
                                # Assign tag to content
                                new_content.tags.append(tag)
                            else:
                                logging.warning(f"Tag '{tag_name}' not found in database - skipping")
                
                session.commit()
                
                # Prepare response
                result_data = {
                    'id': new_content.id,
                    'title': new_content.title,
                    'subject': new_content.subject,
                    'content_type': new_content.content_type,
                    'description': new_content.description,
                    'grade_level': new_content.grade_level,
                    'difficulty_level': new_content.difficulty_level,
                    'duration': new_content.duration,
                    'keywords': new_content.keywords,
                    'file_path': new_content.file_path,
                    'original_filename': new_content.original_filename,
                    'file_size': new_content.file_size,
                    'tags': [tag.name for tag in new_content.tags],
                    'auto_processed': True,
                    'metadata': processing_result.get('metadata', {})
                }
                
                session.close()
                
                logging.info(f"✅ Auto-upload successful: {file.filename} -> {new_content.title}")
                
                return jsonify({
                    'status': 'success',
                    'message': 'File auto-uploaded and processed successfully',
                    'data': result_data
                }), 201
                
            except Exception as e:
                session.rollback()
                session.close()
                # Clean up file if database operation failed
                try:
                    os.remove(file_path)
                except:
                    pass
                raise e
                
        except RequestEntityTooLarge:
            return jsonify({
                'status': 'error',
                'message': f'File too large. Maximum size is {app.config["MAX_CONTENT_LENGTH"] // (1024*1024)}MB'
            }), 413
        except Exception as e:
            logging.error(f"Auto-upload error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/content/<int:content_id>/download', methods=['GET'])
    def download_content(content_id):
        """Download a file by content ID - Task 1.2"""
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                # Get content record
                content = session.query(Content).filter(Content.id == content_id).first()
                
                if not content:
                    session.close()
                    return jsonify({
                        'status': 'error',
                        'message': 'Content not found'
                    }), 404
                
                if not content.file_path:
                    session.close()
                    return jsonify({
                        'status': 'error',
                        'message': 'No file associated with this content'
                    }), 404
                
                # Construct full file path
                full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], content.file_path)
                
                # Check if file exists on disk
                if not os.path.exists(full_file_path):
                    session.close()
                    logging.error(f"File not found on disk: {full_file_path}")
                    return jsonify({
                        'status': 'error',
                        'message': 'File not found on server'
                    }), 404
                
                session.close()
                
                # Prepare download filename (use original filename if available)
                download_filename = content.original_filename or os.path.basename(content.file_path)
                
                try:
                    # Stream file with proper headers
                    return send_file(
                        full_file_path,
                        as_attachment=True,
                        download_name=download_filename,
                        mimetype=content.mime_type or 'application/octet-stream'
                    )
                except Exception as e:
                    logging.error(f"Error sending file: {e}")
                    return jsonify({
                        'status': 'error',
                        'message': 'Error sending file'
                    }), 500
                    
            except Exception as e:
                session.close()
                raise e
                
        except Exception as e:
            logging.error(f"Download error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/content/<int:content_id>', methods=['PUT'])
    def update_content(content_id):
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'No data provided'
                }), 400
            
            # Validate subject if provided
            valid_subjects = ['English', 'Religious Education', 'Learning Support', 'Other']
            if 'subject' in data and data['subject'] and data['subject'] not in valid_subjects:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid subject. Must be one of: {", ".join(valid_subjects)}'
                }), 400
            
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                content = session.query(Content).filter(Content.id == content_id).first()
                
                if not content:
                    session.close()
                    return jsonify({
                        'status': 'error',
                        'message': 'Content not found'
                    }), 404
                
                # Update fields
                if 'title' in data:
                    content.title = data['title']
                if 'content_type' in data:
                    content.content_type = data['content_type']  # Optional - can be set to NULL
                if 'subject' in data:
                    content.subject = data['subject']
                    # Auto-update category if subject changed
                    if data['subject']:
                        category = session.query(Category).filter(Category.name == data['subject']).first()
                        if category:
                            content.category_id = category.id
                if 'description' in data:
                    content.description = data['description']
                if 'content' in data:
                    content.content = data['content']
                if 'grade_level' in data:
                    content.grade_level = data['grade_level']
                if 'duration' in data:
                    content.duration = data['duration']
                if 'keywords' in data:
                    content.keywords = data['keywords']
                if 'category_id' in data:
                    content.category_id = data['category_id']
                
                session.commit()
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Content updated successfully'
                })
            except Exception as e:
                session.rollback()
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/content/<int:content_id>', methods=['DELETE'])
    def delete_content(content_id):
        """Delete content and associated file - Task 1.3 Enhanced"""
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                content = session.query(Content).filter(Content.id == content_id).first()
                
                if not content:
                    session.close()
                    return jsonify({
                        'status': 'error',
                        'message': 'Content not found'
                    }), 404
                
                # Store file information before deletion
                file_path = content.file_path
                file_deleted = False
                file_missing = False
                
                # Try to delete associated file if it exists
                if file_path:
                    full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_path)
                    if os.path.exists(full_file_path):
                        try:
                            os.remove(full_file_path)
                            file_deleted = True
                            logging.info(f"File deleted successfully: {full_file_path}")
                        except Exception as e:
                            logging.error(f"Error deleting file {full_file_path}: {e}")
                            # Continue with database deletion even if file deletion fails
                    else:
                        file_missing = True
                        logging.warning(f"File not found on disk during deletion: {full_file_path}")
                
                # Delete database record
                session.delete(content)
                session.commit()
                session.close()
                
                # Prepare response message
                message = 'Content deleted successfully'
                if file_deleted:
                    message += ' (file removed from disk)'
                elif file_missing:
                    message += ' (file was already missing from disk)'
                elif file_path:
                    message += ' (warning: file could not be removed from disk)'
                
                return jsonify({
                    'status': 'success',
                    'message': message,
                    'file_deleted': file_deleted,
                    'file_missing': file_missing
                })
            except Exception as e:
                session.rollback()
                session.close()
                raise e
                
        except Exception as e:
            logging.error(f"Delete error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/tags', methods=['GET'])
    def get_tags():
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                # BEGIN DYNAMIC TAG USAGE COMPUTATION
                tags_with_counts = (
                    session.query(Tag,
                                 func.count(content_tags.c.content_id).label('usage_count'))
                           .outerjoin(content_tags, Tag.id == content_tags.c.tag_id)
                           .group_by(Tag.id)
                           .all()
                )

                tags_data = []
                for tag, usage_count in tags_with_counts:
                    tags_data.append({
                        'id': tag.id,
                        'name': tag.name,
                        'description': getattr(tag, 'description', ''),
                        'color': getattr(tag, 'color', ''),
                        'usage_count': usage_count
                    })
                # END DYNAMIC TAG USAGE COMPUTATION
                
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'data': tags_data
                })
            except Exception as e:
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/tags', methods=['POST'])
    def create_tag():
        try:
            data = request.get_json()
            if not data or not data.get('name'):
                return jsonify({
                    'status': 'error',
                    'message': 'Tag name is required'
                }), 400
            
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                # Check if tag already exists
                existing_tag = session.query(Tag).filter(Tag.name == data['name']).first()
                if existing_tag:
                    session.close()
                    return jsonify({
                        'status': 'error',
                        'message': 'Tag already exists'
                    }), 400
                
                new_tag = Tag(
                    name=data.get('name'),
                    description=data.get('description', ''),
                    color=data.get('color', '')
                )
                
                session.add(new_tag)
                session.commit()
                
                result_data = {
                    'id': new_tag.id,
                    'name': new_tag.name
                }
                
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Tag created successfully',
                    'data': result_data
                }), 201
            except Exception as e:
                session.rollback()
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/tags/<int:tag_id>', methods=['PUT'])
    def update_tag(tag_id):
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'No data provided'
                }), 400
            
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                tag = session.query(Tag).filter(Tag.id == tag_id).first()
                
                if not tag:
                    session.close()
                    return jsonify({
                        'status': 'error',
                        'message': 'Tag not found'
                    }), 404
                
                # Update fields
                if 'name' in data:
                    tag.name = data['name']
                if 'description' in data:
                    tag.description = data['description']
                if 'color' in data:
                    tag.color = data['color']
                
                session.commit()
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Tag updated successfully'
                })
            except Exception as e:
                session.rollback()
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/tags/<int:tag_id>', methods=['DELETE'])
    def delete_tag(tag_id):
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                tag = session.query(Tag).filter(Tag.id == tag_id).first()
                
                if not tag:
                    session.close()
                    return jsonify({
                        'status': 'error',
                        'message': 'Tag not found'
                    }), 404
                
                session.delete(tag)
                session.commit()
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Tag deleted successfully'
                })
            except Exception as e:
                session.rollback()
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # Content-Tag relationship endpoints
    @app.route('/api/content/<int:content_id>/tags', methods=['POST'])
    def assign_tags_to_content(content_id):
        try:
            data = request.get_json()
            if not data or 'tag_ids' not in data:
                return jsonify({
                    'status': 'error',
                    'message': 'tag_ids array is required'
                }), 400
            
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                content = session.query(Content).filter(Content.id == content_id).first()
                if not content:
                    session.close()
                    return jsonify({
                        'status': 'error',
                        'message': 'Content not found'
                    }), 404
                
                # Clear existing tags if replace is true
                if data.get('replace', False):
                    content.tags = []
                
                # Add new tags
                for tag_id in data['tag_ids']:
                    tag = session.query(Tag).filter(Tag.id == tag_id).first()
                    if tag and tag not in content.tags:
                        content.tags.append(tag)
                        # Update tag usage count
                        tag.usage_count = (tag.usage_count or 0) + 1
                
                session.commit()
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Tags assigned successfully'
                })
            except Exception as e:
                session.rollback()
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/content/<int:content_id>/tags/<int:tag_id>', methods=['DELETE'])
    def remove_tag_from_content(content_id, tag_id):
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                content = session.query(Content).filter(Content.id == content_id).first()
                tag = session.query(Tag).filter(Tag.id == tag_id).first()
                
                if not content or not tag:
                    session.close()
                    return jsonify({
                        'status': 'error',
                        'message': 'Content or tag not found'
                    }), 404
                
                if tag in content.tags:
                    content.tags.remove(tag)
                    # Update tag usage count
                    tag.usage_count = max((tag.usage_count or 1) - 1, 0)
                    session.commit()
                
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Tag removed successfully'
                })
            except Exception as e:
                session.rollback()
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/categories', methods=['GET'])
    def get_categories():
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                categories = session.query(Category).all()
                
                categories_data = []
                for category in categories:
                    # Count content items for this subject
                    content_count = session.query(Content).filter(Content.subject == category.name).count()
                    
                    categories_data.append({
                        'id': category.id,
                        'name': category.name,
                        'description': getattr(category, 'description', ''),
                        'parent_id': getattr(category, 'parent_id', None),
                        # Enhanced for subject-based filtering
                        'content_count': content_count,
                        'subject_name': category.name  # Primary field for subject matching
                    })
                
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'data': categories_data
                })
            except Exception as e:
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/categories/tree', methods=['GET'])
    def get_categories_tree():
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                categories = session.query(Category).all()
                
                # Build tree structure (simple implementation)
                categories_dict = {}
                for category in categories:
                    categories_dict[category.id] = {
                        'id': category.id,
                        'name': category.name,
                        'description': getattr(category, 'description', ''),
                        'parent_id': getattr(category, 'parent_id', None),
                        'children': []
                    }
                
                # Build tree hierarchy
                tree = []
                for category in categories_dict.values():
                    if category['parent_id'] is None:
                        tree.append(category)
                    else:
                        parent = categories_dict.get(category['parent_id'])
                        if parent:
                            parent['children'].append(category)
                
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'data': tree
                })
            except Exception as e:
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/categories', methods=['POST'])
    def create_category():
        try:
            data = request.get_json()
            if not data or not data.get('name'):
                return jsonify({
                    'status': 'error',
                    'message': 'Category name is required'
                }), 400
            
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                new_category = Category(
                    name=data.get('name'),
                    description=data.get('description', ''),
                    parent_id=data.get('parent_id')
                )
                
                session.add(new_category)
                session.commit()
                
                result_data = {
                    'id': new_category.id,
                    'name': new_category.name
                }
                
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Category created successfully',
                    'data': result_data
                }), 201
            except Exception as e:
                session.rollback()
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/categories/<int:category_id>', methods=['PUT'])
    def update_category(category_id):
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'No data provided'
                }), 400
            
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                category = session.query(Category).filter(Category.id == category_id).first()
                
                if not category:
                    session.close()
                    return jsonify({
                        'status': 'error',
                        'message': 'Category not found'
                    }), 404
                
                # Update fields
                if 'name' in data:
                    category.name = data['name']
                if 'description' in data:
                    category.description = data['description']
                if 'parent_id' in data:
                    category.parent_id = data['parent_id']
                
                session.commit()
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Category updated successfully'
                })
            except Exception as e:
                session.rollback()
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/categories/<int:category_id>', methods=['DELETE'])
    def delete_category(category_id):
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                category = session.query(Category).filter(Category.id == category_id).first()
                
                if not category:
                    session.close()
                    return jsonify({
                        'status': 'error',
                        'message': 'Category not found'
                    }), 404
                
                session.delete(category)
                session.commit()
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Category deleted successfully'
                })
            except Exception as e:
                session.rollback()
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # Phase 2: Enhanced subjects API for new category system
    @app.route('/api/subjects', methods=['GET'])
    def get_subjects():
        """
        Returns the new subject categories for frontend dropdowns and validation
        Enhanced with content counts and proper validation data
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            try:
                # Get all current categories (our new subjects)
                categories = session.query(Category).all()
                
                subjects_data = []
                valid_subjects = ['English', 'Religious Education', 'Learning Support', 'Other']
                
                for category in categories:
                    # Only include our main subject categories
                    if category.name in valid_subjects:
                        # Count content items for this subject
                        content_count = session.query(Content).filter(Content.subject == category.name).count()
                        
                        subjects_data.append({
                            'id': category.id,
                            'name': category.name,
                            'description': getattr(category, 'description', ''),
                            'content_count': content_count,
                            'subject_name': category.name,  # Primary field for filtering
                            'is_valid_subject': True  # Flag for frontend validation
                        })
                
                # Sort by name for consistent ordering
                subjects_data.sort(key=lambda x: x['name'])
                
                session.close()
                
                return jsonify({
                    'status': 'success',
                    'data': subjects_data,
                    'valid_subjects': valid_subjects,  # For frontend validation
                    'message': 'New subject categories retrieved successfully'
                })
            except Exception as e:
                session.close()
                raise e
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/admin/cleanup', methods=['POST'])
    def admin_cleanup():
        """Admin endpoint to clean up orphaned files - Task 3.3"""
        try:
            cleanup_result = cleanup_orphaned_files()
            
            return jsonify({
                'status': 'success',
                'message': 'Cleanup completed',
                'data': cleanup_result
            })
            
        except Exception as e:
            logging.error(f"Admin cleanup error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # Serve frontend files
    @app.route('/')
    def serve_index():
        return send_file(frontend_dir / 'index.html')
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        try:
            # Handle API routes first
            if filename.startswith('api/'):
                return jsonify({'error': 'API endpoint not found'}), 404
            
            # Security check - prevent directory traversal
            if '..' in filename or filename.startswith('/'):
                return jsonify({'error': 'Invalid file path'}), 400
            
            file_path = frontend_dir / filename
            if file_path.exists() and file_path.is_file():
                return send_file(file_path)
            else:
                # For SPA routing, return index.html for non-API routes
                return send_file(frontend_dir / 'index.html')
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app

if __name__ == '__main__':
    print("Starting Simplified Teaching Content Database API...")
    print("Direct SQLAlchemy implementation (no service layer)")
    print("=" * 50)
    
    app = create_simple_app()
    
    print("Simplified Flask app created")
    print("Starting server on http://127.0.0.1:5000")
    print("Health check: http://127.0.0.1:5000/api/health")
    print("Content list: http://127.0.0.1:5000/api/content")
    print("=" * 50)
    
    app.run(
        debug=False,  # Disable debug mode for easier process management
        host='127.0.0.1',
        port=5000
    ) 