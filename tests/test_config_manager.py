#!/usr/bin/env python3
"""
Unit tests for the unified ConfigManager
"""

import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import (
    ConfigManager, ConfigValue, EnvConfigSource, JSONConfigSource,
    MarkdownConfigSource, DefaultConfigSource, get_config_manager,
    get_config, reload_config, validate_config
)


class TestConfigValue:
    """Test ConfigValue dataclass"""
    
    def test_config_value_creation(self):
        cv = ConfigValue(value=42, source='test', priority=10)
        assert cv.value == 42
        assert cv.source == 'test'
        assert cv.priority == 10
        assert cv.timestamp is not None


class TestDefaultConfigSource:
    """Test default configuration source"""
    
    def test_default_values(self):
        source = DefaultConfigSource()
        
        # Test some default values
        assert source.get('max_heart_rate').value == 180
        assert source.get('ftp').value == 250
        assert source.get('lthr').value == 165
        assert source.get('ai_provider').value == 'auto'
        assert source.get('use_sport_config').value == True
        
    def test_priority(self):
        source = DefaultConfigSource()
        assert source.priority == 0  # Lowest priority
    
    def test_get_all(self):
        source = DefaultConfigSource()
        all_values = source.get_all()
        assert len(all_values) > 0
        assert 'max_heart_rate' in all_values


class TestEnvConfigSource:
    """Test environment variable configuration source"""
    
    def test_env_loading(self):
        # Set some test environment variables
        os.environ['MAX_HEART_RATE'] = '190'
        os.environ['FTP'] = '300'
        
        source = EnvConfigSource()
        
        # Check values were loaded
        assert source.get('max_heart_rate').value == 190
        assert source.get('ftp').value == 300
        
        # Clean up
        del os.environ['MAX_HEART_RATE']
        del os.environ['FTP']
    
    def test_env_file_loading(self):
        # Create a temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write('TEST_MAX_HEART_RATE=200\n')
            f.write('TEST_FTP=350\n')
            f.write('# This is a comment\n')
            f.write('TEST_BOOL=true\n')
            env_file = f.name
        
        try:
            # Load from the temp file
            source = EnvConfigSource(env_file)
            
            # Note: Since we map specific env vars, these won't be loaded
            # unless they match our mapping
            
        finally:
            os.unlink(env_file)
    
    def test_value_conversion(self):
        source = EnvConfigSource()
        
        # Test integer conversion
        assert source._convert_value('123') == 123
        
        # Test float conversion
        assert source._convert_value('123.45') == 123.45
        
        # Test boolean conversion
        assert source._convert_value('true') == True
        assert source._convert_value('false') == False
        assert source._convert_value('yes') == True
        assert source._convert_value('no') == False
        
        # Test string fallback
        assert source._convert_value('hello') == 'hello'
    
    def test_priority(self):
        source = EnvConfigSource()
        assert source.priority == 100  # Highest priority


class TestJSONConfigSource:
    """Test JSON configuration source"""
    
    def test_json_loading(self):
        # Create a temporary JSON config file
        config_data = {
            "version": "1.0.0",
            "user_profile": {
                "philosophy": "polarized",
                "volume_levels": {"low": 5, "medium": 10, "high": 15},
                "thresholds": {"ftp": 280, "lthr": 160}
            },
            "sports": []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            json_file = f.name
        
        try:
            source = JSONConfigSource(json_file)
            
            # Check values were loaded
            assert source.get('ftp').value == 280
            assert source.get('lthr').value == 160
            assert source.get('training_philosophy').value == 'polarized'
            assert source.get('volume_levels').value == {"low": 5, "medium": 10, "high": 15}
            
        finally:
            os.unlink(json_file)
    
    def test_priority(self):
        source = JSONConfigSource()
        assert source.priority == 75


class TestMarkdownConfigSource:
    """Test Markdown configuration source"""
    
    def test_markdown_parsing(self):
        # Create a temporary markdown file
        markdown_content = """
# My Workout Preferences

## Current Stats
- Current FTP: 295 watts
- Max Heart Rate: 185 bpm
- LTHR: 165 bpm

## Weekly Volume
- Total Training Hours: 12 hours per week

## Equipment
I use a Peloton bike and Concept2 RowERG for my training.
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(markdown_content)
            md_file = f.name
        
        try:
            source = MarkdownConfigSource([md_file])
            
            # Check parsed values
            assert source.get('ftp').value == 295
            assert source.get('max_heart_rate').value == 185
            assert source.get('lthr').value == 165
            assert source.get('weekly_training_hours').value == 12
            assert 'Peloton' in source.get('equipment').value
            assert 'Concept2 RowERG' in source.get('equipment').value
            
        finally:
            os.unlink(md_file)
    
    def test_priority(self):
        source = MarkdownConfigSource()
        assert source.priority == 50


class TestConfigManager:
    """Test the main ConfigManager class"""
    
    def test_priority_resolution(self):
        """Test that higher priority sources override lower ones"""
        # Create temp files for testing
        json_config = {
            "user_profile": {
                "thresholds": {"ftp": 260, "lthr": 155}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_config, f)
            json_file = f.name
        
        try:
            # Set environment variable (highest priority)
            os.environ['FTP'] = '300'
            
            # Create custom sources
            json_source = JSONConfigSource(json_file)
            env_source = EnvConfigSource()
            default_source = DefaultConfigSource()
            
            # Create manager with sources
            manager = ConfigManager(custom_sources=[])
            
            # FTP should come from environment (highest priority)
            assert manager.get('ftp') == 300
            
            # LTHR should come from JSON (no env override)
            assert manager.get('lthr') == 155
            
            # Clean up
            del os.environ['FTP']
            
        finally:
            os.unlink(json_file)
    
    def test_get_with_metadata(self):
        """Test getting values with metadata"""
        manager = ConfigManager()
        
        # Get a default value with metadata
        cv = manager.get_with_metadata('max_heart_rate')
        assert cv is not None
        assert cv.value == 180
        assert cv.source == 'default'
        assert cv.priority == 0
    
    def test_runtime_set(self):
        """Test setting values at runtime"""
        manager = ConfigManager()
        
        # Set a runtime value
        manager.set('custom_value', 42)
        
        # Should be retrievable
        assert manager.get('custom_value') == 42
        
        # Should have highest priority
        cv = manager.get_with_metadata('custom_value')
        assert cv.priority == 150
        assert cv.source == 'runtime'
    
    def test_validation(self):
        """Test configuration validation"""
        manager = ConfigManager()
        
        # Set required values
        manager.set('strava_client_id', 'test_id')
        manager.set('strava_client_secret', 'test_secret')
        
        is_valid, errors = manager.validate()
        assert is_valid
        assert len(errors) == 0
        
        # Test invalid configuration
        manager.set('lthr', 200)  # Higher than max_hr
        manager.set('max_heart_rate', 180)
        
        is_valid, errors = manager.validate()
        assert not is_valid
        assert any('LTHR' in error for error in errors)
    
    def test_export_config(self):
        """Test configuration export"""
        manager = ConfigManager()
        
        # Export to JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_file = f.name
        
        try:
            manager.export_config(export_file, format='json')
            
            # Check file was created and contains data
            with open(export_file, 'r') as f:
                data = json.load(f)
            
            assert 'default' in data
            assert 'max_heart_rate' in data['default']
            
        finally:
            os.unlink(export_file)
    
    def test_singleton_functions(self):
        """Test the singleton convenience functions"""
        # Get a value
        value = get_config('max_heart_rate')
        assert value == 180
        
        # Reload config
        reload_config()
        
        # Validate
        is_valid, errors = validate_config()
        # Note: Will be invalid without Strava credentials
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)


class TestBackwardCompatibility:
    """Test backward compatibility features"""
    
    def test_env_var_mapping(self):
        """Test that old env var names still work"""
        os.environ['MAX_HEART_RATE'] = '195'
        os.environ['AVERAGE_FTP_HR'] = '170'
        
        manager = ConfigManager()
        manager.reload()
        
        # Old env var names should map to new config keys
        assert manager.get('max_heart_rate') == 195
        assert manager.get('lthr') == 170
        
        # Clean up
        del os.environ['MAX_HEART_RATE']
        del os.environ['AVERAGE_FTP_HR']
    
    def test_sport_config_integration(self):
        """Test sport config integration if available"""
        manager = ConfigManager()
        
        # This will return None if sport_config module not available
        sport = manager.get_sport_config('Cycling')
        # Just verify method exists and doesn't crash
        assert sport is None or hasattr(sport, 'name')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])