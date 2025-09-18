#!/usr/bin/env python3
"""
Script to update all Python files to use timezone manager
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
        
        # Add timezone manager import if not present
        if 'from utils.timezone_manager import' not in content and 'datetime' in content:
            # Find the last import statement
            import_pattern = r'(import\s+[^\n]+\n|from\s+[^\n]+\n)'
            imports = re.findall(import_pattern, content)
            
            if imports:
                last_import = imports[-1]
                timezone_import = "from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now\n"
                content = content.replace(last_import, last_import + timezone_import)
        
        # Replace common datetime patterns
        replacements = [
            # now() -> now()
            (r'\bdatetime\.now\(\)', 'now()'),
            # now().strftime -> format_datetime()
            (r'datetime\.now\(\)\.strftime\(([^)]+)\)', r'format_datetime(now(), \1)'),
            # utc_now() -> utc_now()
            (r'\bdatetime\.utcnow\(\)', 'utc_now()'),
            # utc_now().strftime -> format_utc_datetime()
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
    """Update all Python files in the project."""
    project_root = Path(__file__).parent.parent
    
    # Files to skip
    skip_files = {
        'timezone_sync_service.py',
        'timezone_manager.py',
        'test_timezone_sync.py'
    }
    
    updated_count = 0
    total_count = 0
    
    # Find all Python files
    for py_file in project_root.rglob('*.py'):
        if py_file.name in skip_files:
            continue
        
        total_count += 1
        if update_file_timezone_usage(py_file):
            updated_count += 1
    
    print(f"\nUpdated {updated_count} out of {total_count} Python files")

if __name__ == "__main__":
    main()
