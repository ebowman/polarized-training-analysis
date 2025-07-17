#!/usr/bin/env python3
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
