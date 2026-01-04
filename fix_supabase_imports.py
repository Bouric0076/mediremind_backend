#!/usr/bin/env python3
"""
Script to fix supabase_client import issues across the codebase.
Makes all supabase_client imports optional to handle missing dependencies.
"""

import os
import re

def fix_supabase_imports_in_file(file_path):
    """Fix supabase_client imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match supabase_client imports
        patterns = [
            r'^from supabase_client import (\w+)$',
            r'^from supabase_client import (\w+) as (\w+)$',
            r'^import supabase_client$'
        ]
        
        lines = content.split('\n')
        modified = False
        
        for i, line in enumerate(lines):
            for pattern in patterns:
                match = re.match(pattern, line.strip())
                if match:
                    # Create try/except block for the import
                    if 'import supabase_client' in line:
                        new_lines = [
                            'try:',
                            '    import supabase_client',
                            'except ImportError:',
                            '    supabase_client = None'
                        ]
                    else:
                        import_items = match.group(1)
                        new_lines = [
                            'try:',
                            f'    from supabase_client import {import_items}',
                            'except ImportError:',
                            f'    {import_items} = None'
                        ]
                    
                    # Replace the line with the try/except block
                    lines[i:i+1] = new_lines
                    modified = True
                    break
        
        if modified:
            new_content = '\n'.join(lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed imports in: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix all supabase_client imports"""
    files_to_fix = [
        'notifications/tasks.py',
        'notifications/views.py',
        'notifications/queue_manager.py',
        'notifications/cache_layer.py',
        'notifications/scheduler.py',
        'notifications/monitoring.py',
        'notifications/logging_config.py',
        'notifications/performance.py',
        'notifications/interactive_email_views.py',
        'notifications/failsafe.py',
        'notifications/error_recovery.py',
        'notifications/database_optimization.py',
        'authentication/utils.py',
        'authentication/management/commands/audit_user_sync.py'
    ]
    
    base_path = r'c:\Users\bouri\Documents\Projects\mediremind_backend'
    fixed_count = 0
    
    for file_name in files_to_fix:
        file_path = os.path.join(base_path, file_name)
        if os.path.exists(file_path):
            if fix_supabase_imports_in_file(file_path):
                fixed_count += 1
        else:
            print(f"File not found: {file_path}")
    
    print(f"\nFixed imports in {fixed_count} files.")

if __name__ == '__main__':
    main()