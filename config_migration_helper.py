#!/usr/bin/env python3
"""
Configuration Migration Helper

This module helps migrate the PolarFlow application from scattered
configuration sources to the unified ConfigManager.

It provides utilities to:
1. Update existing code to use ConfigManager
2. Validate backward compatibility
3. Generate migration reports
"""

import os
import ast
import json
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
import re
from datetime import datetime

from config_manager import ConfigManager, get_config_manager


class ConfigMigrationAnalyzer:
    """Analyzes codebase for configuration usage patterns"""
    
    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)
        self.config_patterns = {
            'env_access': [
                re.compile(r'os\.getenv\(["\'](\w+)["\']'),
                re.compile(r'os\.environ\[["\'](\w+)["\']'),
                re.compile(r'os\.environ\.get\(["\'](\w+)["\']')
            ],
            'hardcoded': [
                re.compile(r'MAX_HEART_RATE.*=.*(\d+)'),
                re.compile(r'FTP.*=.*(\d+)'),
                re.compile(r'LTHR.*=.*(\d+)'),
                re.compile(r'DEFAULT_.*=.*["\']?(\w+)["\']?')
            ],
            'sport_config': [
                re.compile(r'SportConfigService\(\)'),
                re.compile(r'sport_config_service\.(\w+)\(')
            ]
        }
    
    def analyze_file(self, file_path: Path) -> Dict[str, List[Tuple[int, str, str]]]:
        """Analyze a single Python file for configuration usage"""
        findings = {
            'env_access': [],
            'hardcoded': [],
            'sport_config': []
        }
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            for line_no, line in enumerate(lines, 1):
                # Check environment access
                for pattern in self.config_patterns['env_access']:
                    matches = pattern.findall(line)
                    for match in matches:
                        findings['env_access'].append((line_no, match, line.strip()))
                
                # Check hardcoded values
                for pattern in self.config_patterns['hardcoded']:
                    matches = pattern.findall(line)
                    for match in matches:
                        findings['hardcoded'].append((line_no, match, line.strip()))
                
                # Check sport config usage
                for pattern in self.config_patterns['sport_config']:
                    if pattern.search(line):
                        findings['sport_config'].append((line_no, '', line.strip()))
        
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
        
        return findings
    
    def analyze_project(self) -> Dict[str, Dict]:
        """Analyze entire project for configuration usage"""
        results = {}
        
        # Find all Python files
        python_files = list(self.project_root.glob('**/*.py'))
        
        # Exclude virtual environment and cache directories
        python_files = [
            f for f in python_files 
            if 'venv' not in str(f) and '__pycache__' not in str(f)
        ]
        
        for file_path in python_files:
            findings = self.analyze_file(file_path)
            if any(findings.values()):  # Only include files with findings
                results[str(file_path.relative_to(self.project_root))] = findings
        
        return results
    
    def generate_report(self, output_file: str = 'config_migration_report.md'):
        """Generate a migration report"""
        results = self.analyze_project()
        
        with open(output_file, 'w') as f:
            f.write("# Configuration Migration Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            
            # Summary
            total_env = sum(len(r['env_access']) for r in results.values())
            total_hardcoded = sum(len(r['hardcoded']) for r in results.values())
            total_sport_config = sum(len(r['sport_config']) for r in results.values())
            
            f.write("## Summary\n\n")
            f.write(f"- Files analyzed: {len(results)}\n")
            f.write(f"- Environment accesses: {total_env}\n")
            f.write(f"- Hardcoded values: {total_hardcoded}\n")
            f.write(f"- Sport config usages: {total_sport_config}\n\n")
            
            # Detailed findings
            f.write("## Detailed Findings\n\n")
            
            for file_path, findings in sorted(results.items()):
                f.write(f"### {file_path}\n\n")
                
                if findings['env_access']:
                    f.write("#### Environment Variable Access\n")
                    for line_no, var_name, code in findings['env_access']:
                        f.write(f"- Line {line_no}: `{var_name}` - `{code}`\n")
                    f.write("\n")
                
                if findings['hardcoded']:
                    f.write("#### Hardcoded Values\n")
                    for line_no, value, code in findings['hardcoded']:
                        f.write(f"- Line {line_no}: `{value}` - `{code}`\n")
                    f.write("\n")
                
                if findings['sport_config']:
                    f.write("#### Sport Config Usage\n")
                    for line_no, _, code in findings['sport_config']:
                        f.write(f"- Line {line_no}: `{code}`\n")
                    f.write("\n")
            
            # Migration recommendations
            f.write("## Migration Recommendations\n\n")
            f.write("1. Replace `os.getenv()` calls with `config_manager.get()`\n")
            f.write("2. Move hardcoded defaults to `DefaultConfigSource`\n")
            f.write("3. Ensure backward compatibility by maintaining environment variable names\n")
            f.write("4. Update imports to use `from config_manager import get_config`\n")
        
        print(f"Migration report generated: {output_file}")


class ConfigMigrationHelper:
    """Helps with actual code migration"""
    
    @staticmethod
    def create_compatibility_wrapper(output_file: str = 'config_compat.py'):
        """Create a compatibility wrapper for gradual migration"""
        wrapper_code = '''#!/usr/bin/env python3
"""
Configuration Compatibility Wrapper

This module provides backward compatibility during the migration
to the unified ConfigManager. It intercepts old configuration
access patterns and redirects them to the new system.
"""

import os
from config_manager import get_config_manager

# Create global config manager instance
_config = get_config_manager()

# Compatibility functions that match old patterns
def get_env(key: str, default: str = None) -> str:
    """Backward compatible environment variable access"""
    # Map old environment variable names to new config keys
    env_to_config_map = {
        'MAX_HEART_RATE': 'max_heart_rate',
        'FTP': 'ftp',
        'AVERAGE_FTP_HR': 'lthr',
        'MAX_FTP_HR': 'max_ftp_hr',
        'AVERAGE_FTP_POWER': 'average_ftp_power',
        'STRAVA_CLIENT_ID': 'strava_client_id',
        'STRAVA_CLIENT_SECRET': 'strava_client_secret',
        'AI_PROVIDER': 'ai_provider',
        'OPENAI_API_KEY': 'openai_api_key',
        'ANTHROPIC_API_KEY': 'anthropic_api_key',
        'FLASK_SECRET_KEY': 'flask_secret_key',
        'USE_SPORT_CONFIG': 'use_sport_config'
    }
    
    config_key = env_to_config_map.get(key, key.lower())
    value = _config.get(config_key, default)
    
    # Convert to string to match os.getenv behavior
    if value is not None:
        return str(value)
    return default


# Monkey patch os.getenv for backward compatibility
_original_getenv = os.getenv
def _compat_getenv(key: str, default=None):
    """Intercept getenv calls and redirect to ConfigManager"""
    # First try the new config system
    result = get_env(key, None)
    if result is not None:
        return result
    # Fall back to original getenv
    return _original_getenv(key, default)

# Apply monkey patch
os.getenv = _compat_getenv


# Sport config compatibility
class SportConfigServiceCompat:
    """Compatibility wrapper for SportConfigService"""
    
    def __init__(self, config_path: Optional[str] = None):
        self._config = get_config_manager()
    
    def get_sport_by_activity_type(self, activity_type: str):
        return self._config.get_sport_by_activity_type(activity_type)
    
    def get_sport_by_name(self, name: str):
        return self._config.get_sport_config(name)
    
    def get_threshold_value(self, sport, metric_type):
        # This needs the actual sport config implementation
        if hasattr(sport, 'primary_metric'):
            threshold_field = sport.primary_metric.threshold_field
            return self._config.get(threshold_field)
        return None
    
    def update_threshold(self, threshold_field: str, value: float):
        self._config.set(threshold_field, value)


# Export compatibility interfaces
__all__ = ['get_env', 'SportConfigServiceCompat']
'''
        
        with open(output_file, 'w') as f:
            f.write(wrapper_code)
        
        print(f"Compatibility wrapper created: {output_file}")
    
    @staticmethod
    def update_imports_in_file(file_path: str, dry_run: bool = True):
        """Update imports in a Python file to use ConfigManager"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Add config_manager import if using os.getenv
            if 'os.getenv' in content and 'from config_manager import' not in content:
                # Find the last import statement
                import_lines = []
                lines = content.split('\n')
                last_import_idx = 0
                
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        last_import_idx = i
                
                # Add new import after last import
                lines.insert(last_import_idx + 1, 'from config_manager import get_config')
                content = '\n'.join(lines)
            
            # Replace os.getenv calls
            # This is a simplified replacement - in practice, you'd want more sophisticated AST manipulation
            env_replacements = {
                'MAX_HEART_RATE': 'max_heart_rate',
                'FTP': 'ftp',
                'AVERAGE_FTP_HR': 'lthr',
                'STRAVA_CLIENT_ID': 'strava_client_id',
                'STRAVA_CLIENT_SECRET': 'strava_client_secret',
            }
            
            for env_var, config_key in env_replacements.items():
                # Simple pattern replacement - would need more sophisticated handling for production
                pattern = f'os.getenv("{env_var}"'
                replacement = f'get_config("{config_key}"'
                content = content.replace(pattern, replacement)
                
                pattern = f"os.getenv('{env_var}'"
                content = content.replace(pattern, replacement)
            
            if content != original_content:
                if dry_run:
                    print(f"Would update: {file_path}")
                    print("Changes:")
                    # Show diff (simplified)
                    if 'from config_manager import' in content and 'from config_manager import' not in original_content:
                        print("  + Added config_manager import")
                    print(f"  + Replaced os.getenv calls")
                else:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"Updated: {file_path}")
            
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
    
    @staticmethod
    def validate_migration():
        """Validate that the migration maintains backward compatibility"""
        config = get_config_manager()
        
        # Test that all expected keys are present
        required_keys = [
            'max_heart_rate', 'ftp', 'lthr', 'strava_client_id',
            'strava_client_secret', 'ai_provider', 'flask_secret_key'
        ]
        
        missing_keys = []
        for key in required_keys:
            if config.get(key) is None:
                # Check if it exists in environment
                env_key = key.upper()
                if os.getenv(env_key) is None:
                    missing_keys.append(key)
        
        if missing_keys:
            print(f"Warning: Missing configuration keys: {missing_keys}")
        else:
            print("✓ All required configuration keys are available")
        
        # Validate configuration
        is_valid, errors = config.validate()
        if not is_valid:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✓ Configuration validation passed")
        
        # Test source priority
        print("\nConfiguration sources and priorities:")
        for source, configs in config.get_all_by_source().items():
            print(f"  {source}: {len(configs)} values")
        
        return len(missing_keys) == 0 and is_valid


def main():
    """Run migration analysis and generate helpers"""
    print("PolarFlow Configuration Migration Helper\n")
    
    # Analyze current configuration usage
    print("1. Analyzing configuration usage...")
    analyzer = ConfigMigrationAnalyzer()
    analyzer.generate_report()
    
    # Create compatibility wrapper
    print("\n2. Creating compatibility wrapper...")
    ConfigMigrationHelper.create_compatibility_wrapper()
    
    # Validate current configuration
    print("\n3. Validating configuration...")
    ConfigMigrationHelper.validate_migration()
    
    print("\nMigration helper complete. Check config_migration_report.md for details.")


if __name__ == "__main__":
    main()