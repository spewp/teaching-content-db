"""
Content Analysis API - Enhanced with Task 2.1: Local LLM Integration
Intelligent auto-categorization for educational content using ContentAnalyzer service
"""

import logging
from typing import Dict, Any, Optional

# Import the new ContentAnalyzer service (Task 2.1)
from services.content_analyzer import ContentAnalyzer

# Initialize global ContentAnalyzer instance
content_analyzer = ContentAnalyzer()

# Export categories for backward compatibility
from services.content_analyzer import (
    EDUCATIONAL_CATEGORIES,
    SUBJECT_AREAS, 
    DIFFICULTY_LEVELS,
    GRADE_TARGETS
)

# Backward compatibility functions - now use ContentAnalyzer service
def extract_text_from_file(file_path: str, mime_type: Optional[str] = None) -> str:
    """Extract text content from various file formats - uses ContentAnalyzer service"""
    return content_analyzer.extract_text_from_file(file_path, mime_type)

def analyze_educational_content(title: str, content: str, filename: str = "", 
                              client: Any = None, model: str = "qwen2.5:7b") -> Dict[str, Any]:
    """
    Analyze educational content using LLM for intelligent categorization
    Now uses ContentAnalyzer service (Task 2.1)
    """
    return content_analyzer.analyze_educational_content(title, content, filename)

def analyze_content_endpoint(file, metadata: Dict[str, str]) -> Dict[str, Any]:
    """
    Main endpoint function for content analysis
    Now uses ContentAnalyzer service (Task 2.1)
    """
    return content_analyzer.analyze_uploaded_content(file, metadata) 