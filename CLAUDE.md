# Teaching Content Database - Claude Guidelines

## Essentials
- **ALWAYS review the codebase at the beginning of a coding session** - Do not rely on documentation to inform you sufficiently of the codebase.

## File Management Best Practices
- **Always delete test files after use** - Remove any temporary test files, debug scripts, or sample data created during development
- **Clean up unnecessary files** - Remove any files created for testing, debugging, or exploration once they're no longer needed
- **Maintain clean uploads directory** - The `uploads/` folder should only contain legitimate user content, not test artifacts

## Code Style & UI Guidelines
- **Limited emoji use** - Only use emojis when necessary for UI/GUI experiences or user-facing interfaces
- **Consistent file naming** - Follow existing patterns (snake_case for Python, kebab-case for frontend files)
- **Clear variable names** - Use descriptive names that reflect the educational context

## Project Structure
- `backend/` - Python Flask/FastAPI backend with database models
- `frontend/` - HTML/CSS/JS frontend interface  
- `database/` - SQLite database with models for educational content
- `uploads/` - User-uploaded teaching materials (assessments, lesson plans, worksheets, resources)
- `logs/` - Application logs for debugging and monitoring

## Development Workflow
- **Methodical debugging** - Create isolated debug scripts rather than guessing when issues arise
- **Incremental building** - Build minimal working versions before adding complexity
- **Actual verification** - Always test functionality rather than assuming "should work"
- **Parallel approaches** - Maintain multiple solution paths when tackling complex problems

## Database Operations
- **Use proper models** - Work through the defined models in `database/models.py`
- **Validate data integrity** - Always verify database operations completed successfully

## Launcher & Setup
- **Use appropriate launcher** - `smart_launcher_standalone.py` for full functionality
- **Validate setup** - Run `validate_setup.py` to check system health
- **Check dependencies** - Ensure all requirements from `requirements.txt` are installed

## Quality Standards
- **Documentation consistency** - Documentation changes should be added to the same README at all time
- **Error handling** - Implement proper error handling, especially for file operations and database interactions
- **Performance monitoring** - Check logs for performance issues with large file uploads or database operations

## Collaboration Success Patterns
- **Clear requirements** - Define specific, testable requirements before implementation
- **Architectural thinking** - Consider system-wide impacts of changes
- **Domain expertise integration** - Leverage educational context when making design decisions
- **Insistent verification** - Always test and verify functionality works as intended


## Testing Approach
- Create isolated test environments when needed
- Use temporary files in `uploads/temp/` for testing file operations
- Always clean up test data after completion
- Verify functionality with real-world educational content scenarios 