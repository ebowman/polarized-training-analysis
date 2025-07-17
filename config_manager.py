#!/usr/bin/env python3
"""
Unified Configuration Manager for PolarFlow

This module provides a centralized interface for all configuration sources:
- Environment variables (.env files)
- JSON configuration (sport_config.json)
- Markdown preferences (workout_preferences*.md)
- Hardcoded defaults

The ConfigManager implements a priority-based resolution system where
configuration values are resolved in the following order:
1. Environment variables (highest priority)
2. JSON configuration files
3. Markdown preference files
4. Hardcoded defaults (lowest priority)

Usage:
    config = ConfigManager()
    max_hr = config.get('max_heart_rate')
    ftp = config.get('ftp')
    sport_config = config.get_sport_config('Cycling')
"""

import os
import json
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
from datetime import datetime
import logging
from dataclasses import dataclass, field
from enum import Enum

# Try to import sport config if available
try:
    from sport_config import (
        TrainingConfig, SportConfig, UserProfile, ZoneDefinition,
        Equipment, WorkoutTemplate, Metric, MetricType, TrainingPhilosophy,
        ConfigValidator, ConfigLoader, create_default_config
    )
    from sport_config_service import SportConfigService
    HAS_SPORT_CONFIG = True
except ImportError:
    HAS_SPORT_CONFIG = False
    SportConfig = None
    SportConfigService = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConfigValue:
    """Represents a configuration value with metadata"""
    value: Any
    source: str  # Which source provided this value
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 0  # Higher priority values take precedence


class ConfigSource(ABC):
    """Abstract base class for configuration sources"""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Optional[ConfigValue]:
        """Get a configuration value by key"""
        pass
    
    @abstractmethod
    def get_all(self) -> Dict[str, ConfigValue]:
        """Get all configuration values from this source"""
        pass
    
    @abstractmethod
    def reload(self):
        """Reload configuration from source"""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """Priority of this source (higher wins)"""
        pass


class EnvConfigSource(ConfigSource):
    """Configuration source from environment variables"""
    
    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file or '.env'
        self._cache: Dict[str, ConfigValue] = {}
        self.reload()
    
    def reload(self):
        """Reload environment variables"""
        self._cache.clear()
        
        # Load from .env file if it exists
        if os.path.exists(self.env_file):
            self._load_env_file()
        
        # Load from actual environment
        self._load_from_environment()
    
    def _load_env_file(self):
        """Load variables from .env file"""
        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Only add if not already in environment
                        if key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            logger.warning(f"Failed to load .env file: {e}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        # Map environment variable names to config keys
        env_mapping = {
            'STRAVA_CLIENT_ID': 'strava_client_id',
            'STRAVA_CLIENT_SECRET': 'strava_client_secret',
            'MAX_HEART_RATE': 'max_heart_rate',
            'FTP': 'ftp',
            'AVERAGE_FTP_HR': 'lthr',
            'MAX_FTP_HR': 'max_ftp_hr',
            'AVERAGE_FTP_POWER': 'average_ftp_power',
            'AI_PROVIDER': 'ai_provider',
            'OPENAI_API_KEY': 'openai_api_key',
            'ANTHROPIC_API_KEY': 'anthropic_api_key',
            'FLASK_SECRET_KEY': 'flask_secret_key',
            'USE_SPORT_CONFIG': 'use_sport_config'
        }
        
        for env_key, config_key in env_mapping.items():
            value = os.getenv(env_key)
            if value is not None:
                # Try to convert to appropriate type
                converted_value = self._convert_value(value)
                self._cache[config_key] = ConfigValue(
                    value=converted_value,
                    source='environment',
                    priority=self.priority
                )
    
    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type"""
        # Try to convert to int
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try to convert to float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Try to convert to boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        elif value.lower() in ('false', 'no', '0'):
            return False
        
        # Return as string
        return value
    
    def get(self, key: str, default: Any = None) -> Optional[ConfigValue]:
        """Get configuration value"""
        return self._cache.get(key)
    
    def get_all(self) -> Dict[str, ConfigValue]:
        """Get all configuration values"""
        return self._cache.copy()
    
    @property
    def priority(self) -> int:
        return 100  # Highest priority


class JSONConfigSource(ConfigSource):
    """Configuration source from JSON files"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or 'sport_config.json'
        self._cache: Dict[str, ConfigValue] = {}
        self._sport_config_service = None
        
        if HAS_SPORT_CONFIG:
            self._sport_config_service = SportConfigService(self.config_file)
        
        self.reload()
    
    def reload(self):
        """Reload JSON configuration"""
        self._cache.clear()
        
        if not os.path.exists(self.config_file):
            return
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            # Extract user profile data
            if 'user_profile' in data:
                profile = data['user_profile']
                if 'thresholds' in profile:
                    for key, value in profile['thresholds'].items():
                        self._cache[key] = ConfigValue(
                            value=value,
                            source='json_config',
                            priority=self.priority
                        )
                
                if 'philosophy' in profile:
                    self._cache['training_philosophy'] = ConfigValue(
                        value=profile['philosophy'],
                        source='json_config',
                        priority=self.priority
                    )
                
                if 'volume_levels' in profile:
                    self._cache['volume_levels'] = ConfigValue(
                        value=profile['volume_levels'],
                        source='json_config',
                        priority=self.priority
                    )
            
            # Store the entire config for sport-specific queries
            self._cache['_raw_config'] = ConfigValue(
                value=data,
                source='json_config',
                priority=self.priority
            )
            
        except Exception as e:
            logger.warning(f"Failed to load JSON config: {e}")
    
    def get(self, key: str, default: Any = None) -> Optional[ConfigValue]:
        """Get configuration value"""
        return self._cache.get(key)
    
    def get_all(self) -> Dict[str, ConfigValue]:
        """Get all configuration values"""
        return {k: v for k, v in self._cache.items() if not k.startswith('_')}
    
    def get_sport_config(self, sport_name: str) -> Optional[SportConfig]:
        """Get sport-specific configuration"""
        if self._sport_config_service:
            return self._sport_config_service.get_sport_by_name(sport_name)
        return None
    
    def get_sport_by_activity_type(self, activity_type: str) -> Optional[SportConfig]:
        """Get sport configuration by activity type"""
        if self._sport_config_service:
            return self._sport_config_service.get_sport_by_activity_type(activity_type)
        return None
    
    @property
    def priority(self) -> int:
        return 75  # Second highest priority


class MarkdownConfigSource(ConfigSource):
    """Configuration source from Markdown preference files"""
    
    def __init__(self, preference_files: Optional[List[str]] = None):
        self.preference_files = preference_files or [
            'workout_preferences.md',
            'workout_preferences_personal.md',
            'workout_preferences_personal run swim.md'
        ]
        self._cache: Dict[str, ConfigValue] = {}
        self.reload()
    
    def reload(self):
        """Reload markdown preferences"""
        self._cache.clear()
        
        for file_path in self.preference_files:
            if os.path.exists(file_path):
                self._parse_markdown_file(file_path)
    
    def _parse_markdown_file(self, file_path: str):
        """Parse configuration from markdown file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract FTP
            ftp_match = re.search(r'Current FTP[:\s]+(\d+)\s*watts', content, re.IGNORECASE)
            if ftp_match:
                self._cache['ftp'] = ConfigValue(
                    value=int(ftp_match.group(1)),
                    source=f'markdown:{Path(file_path).name}',
                    priority=self.priority
                )
            
            # Extract max heart rate
            max_hr_match = re.search(r'Max Heart Rate[:\s]+(\d+)\s*bpm', content, re.IGNORECASE)
            if max_hr_match:
                self._cache['max_heart_rate'] = ConfigValue(
                    value=int(max_hr_match.group(1)),
                    source=f'markdown:{Path(file_path).name}',
                    priority=self.priority
                )
            
            # Extract LTHR
            lthr_match = re.search(r'LTHR[:\s]+(\d+)\s*bpm', content, re.IGNORECASE)
            if lthr_match:
                self._cache['lthr'] = ConfigValue(
                    value=int(lthr_match.group(1)),
                    source=f'markdown:{Path(file_path).name}',
                    priority=self.priority
                )
            
            # Extract training hours
            hours_match = re.search(r'Total Training Hours[:\s]+(\d+)\s*hours', content, re.IGNORECASE)
            if hours_match:
                self._cache['weekly_training_hours'] = ConfigValue(
                    value=int(hours_match.group(1)),
                    source=f'markdown:{Path(file_path).name}',
                    priority=self.priority
                )
            
            # Extract equipment preferences
            equipment = []
            if 'peloton' in content.lower():
                equipment.append('Peloton')
            if 'concept2' in content.lower() or 'rowerg' in content.lower():
                equipment.append('Concept2 RowERG')
            if 'dumbbells' in content.lower():
                equipment.append('Dumbbells')
            
            if equipment:
                self._cache['equipment'] = ConfigValue(
                    value=equipment,
                    source=f'markdown:{Path(file_path).name}',
                    priority=self.priority
                )
            
            # Store raw content for additional parsing
            self._cache[f'_raw_{Path(file_path).stem}'] = ConfigValue(
                value=content,
                source=f'markdown:{Path(file_path).name}',
                priority=self.priority
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse markdown file {file_path}: {e}")
    
    def get(self, key: str, default: Any = None) -> Optional[ConfigValue]:
        """Get configuration value"""
        return self._cache.get(key)
    
    def get_all(self) -> Dict[str, ConfigValue]:
        """Get all configuration values"""
        return {k: v for k, v in self._cache.items() if not k.startswith('_')}
    
    @property
    def priority(self) -> int:
        return 50  # Medium priority


class DefaultConfigSource(ConfigSource):
    """Configuration source for hardcoded defaults"""
    
    def __init__(self):
        self._defaults = {
            'max_heart_rate': ConfigValue(value=180, source='default', priority=self.priority),
            'ftp': ConfigValue(value=250, source='default', priority=self.priority),
            'lthr': ConfigValue(value=165, source='default', priority=self.priority),
            'max_ftp_hr': ConfigValue(value=0, source='default', priority=self.priority),
            'average_ftp_power': ConfigValue(value=0, source='default', priority=self.priority),
            'ai_provider': ConfigValue(value='auto', source='default', priority=self.priority),
            'use_sport_config': ConfigValue(value=True, source='default', priority=self.priority),
            'training_philosophy': ConfigValue(value='polarized', source='default', priority=self.priority),
            'volume_levels': ConfigValue(
                value={'low': 5, 'medium': 10, 'high': 15},
                source='default',
                priority=self.priority
            ),
            'min_weekly_volume': ConfigValue(value=180, source='default', priority=self.priority),
            'flask_secret_key': ConfigValue(value='dev-secret-key-change-in-production', source='default', priority=self.priority)
        }
    
    def reload(self):
        """No-op for defaults"""
        pass
    
    def get(self, key: str, default: Any = None) -> Optional[ConfigValue]:
        """Get configuration value"""
        return self._defaults.get(key)
    
    def get_all(self) -> Dict[str, ConfigValue]:
        """Get all configuration values"""
        return self._defaults.copy()
    
    @property
    def priority(self) -> int:
        return 0  # Lowest priority


class ConfigManager:
    """
    Unified configuration manager that aggregates multiple sources
    and provides a single interface for configuration access.
    """
    
    def __init__(self, custom_sources: Optional[List[ConfigSource]] = None):
        """
        Initialize the configuration manager.
        
        Args:
            custom_sources: Optional list of custom configuration sources
        """
        self._sources: List[ConfigSource] = []
        self._cache: Dict[str, ConfigValue] = {}
        
        # Initialize default sources
        self._sources.append(DefaultConfigSource())
        self._sources.append(MarkdownConfigSource())
        self._sources.append(JSONConfigSource())
        self._sources.append(EnvConfigSource())
        
        # Add any custom sources
        if custom_sources:
            self._sources.extend(custom_sources)
        
        # Sort by priority
        self._sources.sort(key=lambda s: s.priority)
        
        # Load all configurations
        self.reload()
    
    def reload(self):
        """Reload all configuration sources"""
        self._cache.clear()
        
        # Reload each source
        for source in self._sources:
            source.reload()
        
        # Build cache with priority resolution
        for source in self._sources:
            for key, config_value in source.get_all().items():
                existing = self._cache.get(key)
                if existing is None or config_value.priority > existing.priority:
                    self._cache[key] = config_value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        config_value = self._cache.get(key)
        if config_value:
            return config_value.value
        return default
    
    def get_with_metadata(self, key: str) -> Optional[ConfigValue]:
        """
        Get a configuration value with its metadata.
        
        Args:
            key: Configuration key
            
        Returns:
            ConfigValue object or None
        """
        return self._cache.get(key)
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            Dictionary of configuration values
        """
        return {key: cv.value for key, cv in self._cache.items()}
    
    def get_source(self, key: str) -> Optional[str]:
        """
        Get the source of a configuration value.
        
        Args:
            key: Configuration key
            
        Returns:
            Source name or None
        """
        config_value = self._cache.get(key)
        if config_value:
            return config_value.source
        return None
    
    def get_sport_config(self, sport_name: str) -> Optional[SportConfig]:
        """
        Get sport-specific configuration.
        
        Args:
            sport_name: Name of the sport
            
        Returns:
            SportConfig object or None
        """
        # Try to get from JSON source
        for source in self._sources:
            if isinstance(source, JSONConfigSource):
                return source.get_sport_config(sport_name)
        return None
    
    def get_sport_by_activity_type(self, activity_type: str) -> Optional[SportConfig]:
        """
        Get sport configuration by activity type.
        
        Args:
            activity_type: Strava activity type
            
        Returns:
            SportConfig object or None
        """
        # Try to get from JSON source
        for source in self._sources:
            if isinstance(source, JSONConfigSource):
                return source.get_sport_by_activity_type(activity_type)
        return None
    
    def set(self, key: str, value: Any, source: str = 'runtime'):
        """
        Set a configuration value at runtime.
        
        Args:
            key: Configuration key
            value: Configuration value
            source: Source identifier
        """
        self._cache[key] = ConfigValue(
            value=value,
            source=source,
            priority=150  # Runtime values have highest priority
        )
    
    def get_all_by_source(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all configuration values grouped by source.
        
        Returns:
            Dictionary mapping source names to their configuration values
        """
        by_source = {}
        for key, config_value in self._cache.items():
            source = config_value.source
            if source not in by_source:
                by_source[source] = {}
            by_source[source][key] = config_value.value
        return by_source
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the current configuration.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required API keys
        if self.get('ai_provider') != 'none':
            if self.get('ai_provider') == 'openai' and not self.get('openai_api_key'):
                errors.append("OpenAI API key required when AI provider is 'openai'")
            elif self.get('ai_provider') == 'claude' and not self.get('anthropic_api_key'):
                errors.append("Anthropic API key required when AI provider is 'claude'")
        
        # Check Strava credentials
        if not self.get('strava_client_id') or not self.get('strava_client_secret'):
            errors.append("Strava client ID and secret are required")
        
        # Validate thresholds
        max_hr = self.get('max_heart_rate', 0)
        lthr = self.get('lthr', 0)
        if lthr > max_hr:
            errors.append(f"LTHR ({lthr}) cannot be greater than max heart rate ({max_hr})")
        
        ftp = self.get('ftp', 0)
        if ftp < 0:
            errors.append(f"FTP ({ftp}) cannot be negative")
        
        return len(errors) == 0, errors
    
    def export_config(self, file_path: str, format: str = 'json'):
        """
        Export current configuration to a file.
        
        Args:
            file_path: Path to export file
            format: Export format (json, yaml, env)
        """
        config_data = self.get_all_by_source()
        
        if format == 'json':
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
        elif format == 'env':
            with open(file_path, 'w') as f:
                f.write("# Exported configuration\n")
                f.write(f"# Generated at {datetime.now().isoformat()}\n\n")
                for key, value in self.get_all().items():
                    if isinstance(value, (str, int, float, bool)):
                        env_key = key.upper()
                        f.write(f"{env_key}={value}\n")
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Singleton instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


# Convenience functions
def get_config(key: str, default: Any = None) -> Any:
    """Get a configuration value"""
    return get_config_manager().get(key, default)


def reload_config():
    """Reload all configuration sources"""
    get_config_manager().reload()


def validate_config() -> Tuple[bool, List[str]]:
    """Validate the current configuration"""
    return get_config_manager().validate()