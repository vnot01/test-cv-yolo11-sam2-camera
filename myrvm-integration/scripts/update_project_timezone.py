#!/usr/bin/env python3
"""
Script to update only project Python files to use timezone manager
"""

import os
import re
from pathlib import Path

def update_file_timezone_usage(file_path: Path):
    """Update a single file to use timezone manager."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Add timezone manager import if not present and file uses datetime
        if ('from utils.timezone_manager import' not in content and 
            'datetime' in content and 
            ('datetime.now()' in content or 'datetime.utcnow()' in content)):
            
            # Find the last import statement
            import_pattern = r'(import\s+[^\n]+\n|from\s+[^\n]+\n)'
            imports = re.findall(import_pattern, content)
            
            if imports:
                last_import = imports[-1]
                timezone_import = "from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now\n"
                content = content.replace(last_import, last_import + timezone_import)
        
        # Replace common datetime patterns
        replacements = [
            # datetime.now() -> now()
            (r'\bdatetime\.now\(\)', 'now()'),
            # datetime.now().strftime -> format_datetime()
            (r'datetime\.now\(\)\.strftime\(([^)]+)\)', r'format_datetime(now(), \1)'),
            # datetime.utcnow() -> utc_now()
            (r'\bdatetime\.utcnow\(\)', 'utc_now()'),
            # datetime.utcnow().strftime -> format_utc_datetime()
            (r'datetime\.utcnow\(\)\.strftime\(([^)]+)\)', r'format_utc_datetime(utc_now(), \1)'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    """Update only project Python files."""
    project_root = Path(__file__).parent.parent
    
    # Files to skip
    skip_files = {
        'timezone_sync_service.py',
        'timezone_manager.py',
        'test_timezone_sync.py',
        'update_timezone_usage.py',
        'update_project_timezone.py'
    }
    
    # Directories to skip (virtual environment, etc.)
    skip_dirs = {
        'venv',
        '__pycache__',
        '.git',
        'node_modules'
    }
    
    updated_count = 0
    total_count = 0
    
    # Find all Python files in project (not in venv)
    for py_file in project_root.rglob('*.py'):
        # Skip if in venv or other skip directories
        if any(skip_dir in py_file.parts for skip_dir in skip_dirs):
            continue
            
        if py_file.name in skip_files:
            continue
        
        total_count += 1
        if update_file_timezone_usage(py_file):
            updated_count += 1
    
    print(f"\nUpdated {updated_count} out of {total_count} project Python files")

if __name__ == "__main__":
    main()
