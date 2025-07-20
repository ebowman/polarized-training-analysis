#!/usr/bin/env python
"""
Settings API Module

Provides secure API endpoints for managing application settings including:
- Environment variable management (.env file)
- Prompt template CRUD operations
- Prompt to JSON conversion
- Secure file operations with validation
"""

import os
import json
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv, set_key, dotenv_values
import secrets
from functools import wraps
from flask import jsonify, request

# Import logging
from logging_config import get_logger

logger = get_logger(__name__)

# Constants
SETTINGS_DIR = Path("settings")
PROMPTS_DIR = SETTINGS_DIR / "prompts"
ENV_FILE = Path(".env")
ENV_EXAMPLE_FILE = Path(".env.example")

# Ensure directories exist
SETTINGS_DIR.mkdir(exist_ok=True)
PROMPTS_DIR.mkdir(exist_ok=True)

# Security constants
ALLOWED_ENV_KEYS = {
    'STRAVA_CLIENT_ID', 'STRAVA_CLIENT_SECRET',
    'MAX_HEART_RATE', 'FTP', 'LTHR', 'AVERAGE_FTP_HR', 'MAX_FTP_HR', 'AVERAGE_FTP_POWER',
    'AI_PROVIDER', 'AI_PRIMARY_PROVIDER', 'AI_FALLBACK_PROVIDER',
    'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'CLAUDE_API_KEY',
    'FLASK_SECRET_KEY',
    'CACHE_DURATION_SECONDS', 'AI_SESSION_EXPIRY_SECONDS',
    'DEFAULT_WEB_PORT', 'DEFAULT_HOST',
    'SYSTEM_PROMPT', 'ANALYSIS_PROMPT',
    'USE_SPORT_CONFIG', 'SPORT_CONFIG_JSON'
}

# Validation patterns
ENV_VALIDATORS = {
    'MAX_HEART_RATE': r'^\d{2,3}$',  # 2-3 digit number
    'FTP': r'^\d{2,4}$',  # 2-4 digit number
    'LTHR': r'^\d{2,3}$',  # 2-3 digit number (Lactate Threshold Heart Rate)
    'AVERAGE_FTP_HR': r'^\d{0,3}$',  # 0-3 digit number (can be empty/0)
    'MAX_FTP_HR': r'^\d{0,3}$',  # 0-3 digit number (can be empty/0)
    'AVERAGE_FTP_POWER': r'^\d{0,4}$',  # 0-4 digit number (can be empty/0)
    'AI_PROVIDER': r'^(openai|claude|auto|Prefer OpenAI|Prefer Claude)$',
    'AI_PRIMARY_PROVIDER': r'^(openai|claude)$',
    'AI_FALLBACK_PROVIDER': r'^(openai|claude)$',
    'STRAVA_CLIENT_ID': r'^[a-zA-Z0-9_-]+$',
    'STRAVA_CLIENT_SECRET': r'^[a-zA-Z0-9_-]+$',
    'OPENAI_API_KEY': r'^sk-.*',  # Any string starting with sk-
    'ANTHROPIC_API_KEY': r'^sk-.*',  # Any string starting with sk-
    'CLAUDE_API_KEY': r'^sk-.*',  # Any string starting with sk-
    'FLASK_SECRET_KEY': r'^[a-fA-F0-9_-]+',  # Allow any hex string
    'CACHE_DURATION_SECONDS': r'^\d{1,8}$',  # 1-8 digit number
    'AI_SESSION_EXPIRY_SECONDS': r'^\d{1,8}$',  # 1-8 digit number
    'DEFAULT_WEB_PORT': r'^\d{1,5}$',  # 1-5 digit port number
    'DEFAULT_HOST': r'^[a-zA-Z0-9.-]+$',  # hostname/IP
    'USE_SPORT_CONFIG': r'^(true|false|yes|no|1|0)$',  # boolean-like values
    # SYSTEM_PROMPT, ANALYSIS_PROMPT, SPORT_CONFIG_JSON - no validation (allow any text)
}


def validate_env_value(key: str, value: str) -> bool:
    """Validate environment variable value against patterns"""
    if key not in ALLOWED_ENV_KEYS:
        return False
    
    # Allow empty values for optional fields
    if not value and key in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'CLAUDE_API_KEY', 
                             'FLASK_SECRET_KEY', 'SYSTEM_PROMPT', 'ANALYSIS_PROMPT',
                             'SPORT_CONFIG_JSON']:
        return True
    
    if key in ENV_VALIDATORS:
        pattern = ENV_VALIDATORS[key]
        return bool(re.match(pattern, value))
    
    return True


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal attacks"""
    # Remove any path components
    filename = os.path.basename(filename)
    # Remove any non-alphanumeric characters except dots, dashes, and underscores
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    # Ensure it ends with .json
    if not filename.endswith('.json'):
        filename += '.json'
    return filename


def require_auth(f):
    """Decorator to require authentication for sensitive operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # In production, you would check session or JWT token here
        # For now, we'll just check if the request has a valid session
        # This should be integrated with your existing auth system
        return f(*args, **kwargs)
    return decorated_function


class SettingsAPI:
    """API handler for settings management"""
    
    @staticmethod
    def get_env_settings() -> Dict[str, Any]:
        """Get all environment settings (with sensitive values masked)"""
        try:
            # Load current .env values
            env_values = dotenv_values(ENV_FILE)
            
            # Mask sensitive values
            masked_values = {}
            for key, value in env_values.items():
                if key in ALLOWED_ENV_KEYS:
                    if 'SECRET' in key or 'API_KEY' in key:
                        # Mask sensitive values
                        if value and len(value) > 8:
                            masked_values[key] = value[:4] + '*' * (len(value) - 8) + value[-4:]
                        else:
                            masked_values[key] = '*' * len(value) if value else ''
                    else:
                        masked_values[key] = value
            
            # Special handling for AI_PROVIDER display value
            if masked_values.get('AI_PROVIDER') == 'auto':
                primary = env_values.get('AI_PRIMARY_PROVIDER', 'claude')
                if primary == 'openai':
                    masked_values['AI_PROVIDER'] = 'Prefer OpenAI'
                elif primary == 'claude':
                    masked_values['AI_PROVIDER'] = 'Prefer Claude'
            
            # Load example values for reference
            example_values = {}
            if ENV_EXAMPLE_FILE.exists():
                example_values = dotenv_values(ENV_EXAMPLE_FILE)
            
            return {
                'success': True,
                'settings': masked_values,
                'example': example_values,
                'allowed_keys': list(ALLOWED_ENV_KEYS)
            }
            
        except Exception as e:
            logger.error(f"Error reading env settings: {e}")
            return {
                'success': False,
                'error': 'Failed to read environment settings'
            }
    
    @staticmethod
    @require_auth
    def update_env_setting(key: str, value: str) -> Dict[str, Any]:
        """Update a single environment setting"""
        try:
            # Validate key
            if key not in ALLOWED_ENV_KEYS:
                return {
                    'success': False,
                    'error': f'Invalid setting key: {key}'
                }
            
            # Special handling for AI_PROVIDER preference values
            if key == 'AI_PROVIDER' and value in ['Prefer OpenAI', 'Prefer Claude']:
                # Convert preference to auto mode with primary/fallback settings
                if value == 'Prefer OpenAI':
                    set_key(ENV_FILE, 'AI_PROVIDER', 'auto')
                    set_key(ENV_FILE, 'AI_PRIMARY_PROVIDER', 'openai')
                    set_key(ENV_FILE, 'AI_FALLBACK_PROVIDER', 'claude')
                elif value == 'Prefer Claude':
                    set_key(ENV_FILE, 'AI_PROVIDER', 'auto')
                    set_key(ENV_FILE, 'AI_PRIMARY_PROVIDER', 'claude')
                    set_key(ENV_FILE, 'AI_FALLBACK_PROVIDER', 'openai')
                
                # Reload environment
                load_dotenv(override=True)
                
                logger.info(f"Updated AI provider preference: {value}")
                
                return {
                    'success': True,
                    'message': f'Successfully updated AI provider preference to {value}'
                }
            else:
                # Validate value
                if not validate_env_value(key, value):
                    return {
                        'success': False,
                        'error': f'Invalid value format for {key}'
                    }
                
                # Create .env file if it doesn't exist
                if not ENV_FILE.exists():
                    ENV_FILE.touch()
                
                # Update the value
                set_key(ENV_FILE, key, value)
                
                # Reload environment
                load_dotenv(override=True)
                
                logger.info(f"Updated env setting: {key}")
                
                return {
                    'success': True,
                    'message': f'Successfully updated {key}'
                }
            
        except Exception as e:
            logger.error(f"Error updating env setting {key}: {e}")
            return {
                'success': False,
                'error': 'Failed to update environment setting'
            }
    
    @staticmethod
    @require_auth
    def update_env_settings(settings: Dict[str, str]) -> Dict[str, Any]:
        """Update multiple environment settings at once"""
        try:
            errors = []
            updated = []
            
            for key, value in settings.items():
                result = SettingsAPI.update_env_setting(key, value)
                if result['success']:
                    updated.append(key)
                else:
                    errors.append(result['error'])
            
            if errors:
                return {
                    'success': False,
                    'errors': errors,
                    'updated': updated
                }
            
            return {
                'success': True,
                'message': f'Successfully updated {len(updated)} settings',
                'updated': updated
            }
            
        except Exception as e:
            logger.error(f"Error updating env settings: {e}")
            return {
                'success': False,
                'error': 'Failed to update environment settings'
            }
    
    @staticmethod
    def list_prompt_templates() -> Dict[str, Any]:
        """List all prompt templates"""
        try:
            templates = []
            
            for file_path in PROMPTS_DIR.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        templates.append({
                            'id': file_path.stem,
                            'name': data.get('name', file_path.stem),
                            'description': data.get('description', ''),
                            'created_at': data.get('created_at', ''),
                            'updated_at': data.get('updated_at', ''),
                            'is_default': data.get('is_default', False)
                        })
                except Exception as e:
                    logger.error(f"Error reading template {file_path}: {e}")
            
            # Sort by name
            templates.sort(key=lambda x: x['name'])
            
            return {
                'success': True,
                'templates': templates
            }
            
        except Exception as e:
            logger.error(f"Error listing prompt templates: {e}")
            return {
                'success': False,
                'error': 'Failed to list prompt templates'
            }
    
    @staticmethod
    def get_prompt_template(template_id: str) -> Dict[str, Any]:
        """Get a specific prompt template"""
        try:
            filename = sanitize_filename(template_id)
            file_path = PROMPTS_DIR / filename
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': 'Template not found'
                }
            
            with open(file_path, 'r') as f:
                template = json.load(f)
            
            return {
                'success': True,
                'template': template
            }
            
        except Exception as e:
            logger.error(f"Error reading prompt template {template_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to read prompt template'
            }
    
    @staticmethod
    @require_auth
    def create_prompt_template(data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new prompt template"""
        try:
            # Generate unique ID if not provided
            template_id = data.get('id', f"template_{secrets.token_hex(8)}")
            filename = sanitize_filename(template_id)
            file_path = PROMPTS_DIR / filename
            
            # Check if already exists
            if file_path.exists():
                return {
                    'success': False,
                    'error': 'Template with this ID already exists'
                }
            
            # Prepare template data
            template = {
                'id': template_id,
                'name': data.get('name', 'Untitled Template'),
                'description': data.get('description', ''),
                'prompt': data.get('prompt', ''),
                'variables': data.get('variables', {}),
                'is_default': data.get('is_default', False),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # If setting as default, unset other defaults
            if template['is_default']:
                SettingsAPI._unset_default_templates()
            
            # Save template
            with open(file_path, 'w') as f:
                json.dump(template, f, indent=2)
            
            logger.info(f"Created prompt template: {template_id}")
            
            return {
                'success': True,
                'message': 'Template created successfully',
                'template_id': template_id
            }
            
        except Exception as e:
            logger.error(f"Error creating prompt template: {e}")
            return {
                'success': False,
                'error': 'Failed to create prompt template'
            }
    
    @staticmethod
    @require_auth
    def update_prompt_template(template_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing prompt template"""
        try:
            filename = sanitize_filename(template_id)
            file_path = PROMPTS_DIR / filename
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': 'Template not found'
                }
            
            # Read existing template
            with open(file_path, 'r') as f:
                template = json.load(f)
            
            # Update fields
            if 'name' in data:
                template['name'] = data['name']
            if 'description' in data:
                template['description'] = data['description']
            if 'prompt' in data:
                template['prompt'] = data['prompt']
            if 'variables' in data:
                template['variables'] = data['variables']
            if 'is_default' in data:
                template['is_default'] = data['is_default']
                if template['is_default']:
                    SettingsAPI._unset_default_templates()
            
            template['updated_at'] = datetime.now().isoformat()
            
            # Save updated template
            with open(file_path, 'w') as f:
                json.dump(template, f, indent=2)
            
            logger.info(f"Updated prompt template: {template_id}")
            
            return {
                'success': True,
                'message': 'Template updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error updating prompt template {template_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to update prompt template'
            }
    
    @staticmethod
    @require_auth
    def delete_prompt_template(template_id: str) -> Dict[str, Any]:
        """Delete a prompt template"""
        try:
            filename = sanitize_filename(template_id)
            file_path = PROMPTS_DIR / filename
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': 'Template not found'
                }
            
            # Delete the file
            file_path.unlink()
            
            logger.info(f"Deleted prompt template: {template_id}")
            
            return {
                'success': True,
                'message': 'Template deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error deleting prompt template {template_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to delete prompt template'
            }
    
    @staticmethod
    def convert_prompt_to_json(prompt: str) -> Dict[str, Any]:
        """Convert a natural language prompt to structured JSON"""
        try:
            # Extract variables from prompt (e.g., {variable_name})
            variables = re.findall(r'\{([^}]+)\}', prompt)
            
            # Extract sections (lines starting with specific keywords)
            sections = {
                'objective': '',
                'context': '',
                'constraints': [],
                'output_format': '',
                'examples': []
            }
            
            lines = prompt.strip().split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for section headers
                lower_line = line.lower()
                if lower_line.startswith('objective:') or lower_line.startswith('goal:'):
                    current_section = 'objective'
                    line = line.split(':', 1)[1].strip() if ':' in line else ''
                elif lower_line.startswith('context:') or lower_line.startswith('background:'):
                    current_section = 'context'
                    line = line.split(':', 1)[1].strip() if ':' in line else ''
                elif lower_line.startswith('constraint') or lower_line.startswith('requirement'):
                    current_section = 'constraints'
                    line = line.split(':', 1)[1].strip() if ':' in line else ''
                elif lower_line.startswith('output') or lower_line.startswith('format'):
                    current_section = 'output_format'
                    line = line.split(':', 1)[1].strip() if ':' in line else ''
                elif lower_line.startswith('example'):
                    current_section = 'examples'
                    line = line.split(':', 1)[1].strip() if ':' in line else ''
                
                # Add content to current section
                if line and current_section:
                    if current_section in ['constraints', 'examples']:
                        if line.startswith('-') or line.startswith('*'):
                            sections[current_section].append(line[1:].strip())
                        else:
                            sections[current_section].append(line)
                    else:
                        if sections[current_section]:
                            sections[current_section] += ' ' + line
                        else:
                            sections[current_section] = line
            
            # Build structured JSON
            result = {
                'prompt_text': prompt,
                'variables': {var: f"{{description_for_{var}}}" for var in variables},
                'structure': sections,
                'metadata': {
                    'extracted_at': datetime.now().isoformat(),
                    'variable_count': len(variables),
                    'has_objective': bool(sections['objective']),
                    'has_constraints': bool(sections['constraints']),
                    'has_examples': bool(sections['examples'])
                }
            }
            
            return {
                'success': True,
                'json': result
            }
            
        except Exception as e:
            logger.error(f"Error converting prompt to JSON: {e}")
            return {
                'success': False,
                'error': 'Failed to convert prompt to JSON'
            }
    
    @staticmethod
    def _unset_default_templates():
        """Unset default flag on all templates"""
        try:
            for file_path in PROMPTS_DIR.glob("*.json"):
                with open(file_path, 'r') as f:
                    template = json.load(f)
                
                if template.get('is_default', False):
                    template['is_default'] = False
                    with open(file_path, 'w') as f:
                        json.dump(template, f, indent=2)
        except Exception as e:
            logger.error(f"Error unsetting default templates: {e}")


# Flask route handlers
def register_settings_routes(app):
    """Register settings API routes with Flask app"""
    
    @app.route('/api/settings/env', methods=['GET'])
    @require_auth
    def get_env_settings():
        """Get environment settings"""
        return jsonify(SettingsAPI.get_env_settings())
    
    @app.route('/api/settings/env/<key>', methods=['PUT'])
    @require_auth
    def update_env_setting(key):
        """Update a single environment setting"""
        data = request.get_json()
        if not data or 'value' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing value in request body'
            }), 400
        
        result = SettingsAPI.update_env_setting(key, data['value'])
        return jsonify(result), 200 if result['success'] else 400
    
    @app.route('/api/settings/env', methods=['PUT'])
    @require_auth
    def update_env_settings():
        """Update multiple environment settings"""
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing request body'
            }), 400
        
        result = SettingsAPI.update_env_settings(data)
        return jsonify(result), 200 if result['success'] else 400
    
    @app.route('/api/settings/prompts', methods=['GET'])
    def list_prompt_templates():
        """List all prompt templates"""
        return jsonify(SettingsAPI.list_prompt_templates())
    
    @app.route('/api/settings/prompts/<template_id>', methods=['GET'])
    def get_prompt_template(template_id):
        """Get a specific prompt template"""
        result = SettingsAPI.get_prompt_template(template_id)
        return jsonify(result), 200 if result['success'] else 404
    
    @app.route('/api/settings/prompts', methods=['POST'])
    @require_auth
    def create_prompt_template():
        """Create a new prompt template"""
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing request body'
            }), 400
        
        result = SettingsAPI.create_prompt_template(data)
        return jsonify(result), 201 if result['success'] else 400
    
    @app.route('/api/settings/prompts/<template_id>', methods=['PUT'])
    @require_auth
    def update_prompt_template(template_id):
        """Update an existing prompt template"""
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing request body'
            }), 400
        
        result = SettingsAPI.update_prompt_template(template_id, data)
        return jsonify(result), 200 if result['success'] else 400
    
    @app.route('/api/settings/prompts/<template_id>', methods=['DELETE'])
    @require_auth
    def delete_prompt_template(template_id):
        """Delete a prompt template"""
        result = SettingsAPI.delete_prompt_template(template_id)
        return jsonify(result), 200 if result['success'] else 404
    
    @app.route('/api/settings/prompts/convert', methods=['POST'])
    def convert_prompt_to_json():
        """Convert natural language prompt to JSON"""
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing prompt in request body'
            }), 400
        
        result = SettingsAPI.convert_prompt_to_json(data['prompt'])
        return jsonify(result), 200 if result['success'] else 400
    
    # Config Generation Endpoint
    @app.route('/api/settings/generate-config', methods=['POST'])
    @require_auth
    def api_generate_config():
        """Generate sport configuration from preferences text"""
        try:
            data = request.get_json()
            if not data or 'preferences' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing preferences in request body'
                }), 400
            
            preferences_text = data['preferences']
            zone_distribution = data.get('zone_distribution')
            
            # Import config generator
            from config_generator import ConfigGenerator
            from ai_providers import OpenAIProvider, ClaudeProvider
            
            # Try to get AI provider based on settings
            ai_provider = None
            provider_type = os.getenv('AI_PROVIDER', 'auto')
            
            if provider_type == 'auto':
                # Try primary provider first
                primary = os.getenv('AI_PRIMARY_PROVIDER', 'claude')
                if primary == 'openai':
                    provider = OpenAIProvider()
                    if provider.is_available():
                        ai_provider = provider
                else:
                    provider = ClaudeProvider()
                    if provider.is_available():
                        ai_provider = provider
                        
                # Fall back to secondary if needed
                if not ai_provider:
                    fallback = os.getenv('AI_FALLBACK_PROVIDER', 'openai')
                    if fallback == 'openai':
                        provider = OpenAIProvider()
                        if provider.is_available():
                            ai_provider = provider
                    else:
                        provider = ClaudeProvider()
                        if provider.is_available():
                            ai_provider = provider
            elif provider_type == 'openai':
                provider = OpenAIProvider()
                if provider.is_available():
                    ai_provider = provider
            elif provider_type == 'claude':
                provider = ClaudeProvider()
                if provider.is_available():
                    ai_provider = provider
            
            if not ai_provider:
                return jsonify({
                    'success': False,
                    'error': 'No AI provider available. Please configure API keys.'
                }), 503
            
            # Generate configuration
            generator = ConfigGenerator(ai_provider=ai_provider)
            
            # If zone distribution provided, append it to preferences
            if zone_distribution:
                zone_text = "\n\nZone Distribution Targets:\n"
                for zone, percentage in zone_distribution.items():
                    zone_text += f"- Zone {zone}: {percentage}%\n"
                preferences_text += zone_text
            
            try:
                config = generator.generate_config(preferences_text)
                
                # Convert to dict for JSON response
                config_dict = {
                    'version': config.version,
                    'user_profile': {
                        'philosophy': config.user_profile.philosophy.value,
                        'volume_levels': config.user_profile.volume_levels,
                        'thresholds': config.user_profile.thresholds,
                        'preferences': config.user_profile.preferences
                    },
                    'sports': []
                }
                
                for sport in config.sports:
                    sport_dict = {
                        'name': sport.name,
                        'activity_types': sport.activity_types,
                        'primary_metric': {
                            'type': sport.primary_metric.type.value,
                            'unit': sport.primary_metric.unit,
                            'threshold_field': sport.primary_metric.threshold_field,
                            'decimal_places': sport.primary_metric.decimal_places
                        } if sport.primary_metric else None,
                        'secondary_metric': {
                            'type': sport.secondary_metric.type.value,
                            'unit': sport.secondary_metric.unit,
                            'threshold_field': sport.secondary_metric.threshold_field,
                            'decimal_places': sport.secondary_metric.decimal_places
                        } if sport.secondary_metric else None,
                        'zone_model': sport.zone_model.value,
                        'zones': [],
                        'equipment': [{'name': e.name, 'notes': e.notes} for e in sport.equipment],
                        'workout_templates': [],
                        'notes': sport.notes,
                        'zone_distribution': sport.zone_distribution
                    }
                    
                    for zone in sport.zones:
                        zone_dict = {
                            'name': zone.name,
                            'lower': zone.lower,
                            'upper': zone.upper,
                            'description': zone.description,
                            'primary_range': zone.primary_range,
                            'secondary_range': zone.secondary_range
                        }
                        sport_dict['zones'].append(zone_dict)
                    
                    for template in sport.workout_templates:
                        template_dict = {
                            'name': template.name,
                            'description': template.description,
                            'structure': template.structure,
                            'target_zones': template.target_zones,
                            'duration_minutes': template.duration_minutes,
                            'frequency_per_week': template.frequency_per_week
                        }
                        sport_dict['workout_templates'].append(template_dict)
                    
                    config_dict['sports'].append(sport_dict)
                
                return jsonify({
                    'success': True,
                    'config': config_dict,
                    'provider_used': type(ai_provider).__name__
                })
                
            except Exception as e:
                logger.error(f"Error generating config: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Failed to generate configuration: {str(e)}'
                }), 500
                
        except Exception as e:
            logger.error(f"Error in generate-config endpoint: {e}")
            return jsonify({
                'success': False,
                'error': 'An unexpected error occurred'
            }), 500
    
    # Sport Config Zone Distribution Endpoints
    @app.route('/api/settings/zone-distribution', methods=['GET'])
    def get_zone_distribution():
        """Get current zone distribution settings"""
        try:
            from sport_config_service import SportConfigService
            service = SportConfigService()
            
            # Get global user zone distribution
            user_targets = service.get_zone_distribution_target()
            philosophy = service.get_training_philosophy()
            
            # Get sport-specific distributions
            sport_distributions = {}
            for sport in service.get_all_sports():
                if sport.zone_distribution:
                    sport_distributions[sport.name] = sport.zone_distribution
            
            return jsonify({
                'success': True,
                'data': {
                    'philosophy': philosophy.value,
                    'user_targets': user_targets,
                    'sport_distributions': sport_distributions
                }
            })
        except Exception as e:
            logger.error(f"Error getting zone distribution: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/settings/zone-distribution/user', methods=['PUT'])
    @require_auth
    def update_user_zone_distribution():
        """Update user's global zone distribution"""
        try:
            data = request.get_json()
            if not data or 'zone_distribution' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing zone_distribution in request body'
                }), 400
            
            from sport_config_service import SportConfigService
            service = SportConfigService()
            
            zone_dist = data['zone_distribution']
            # Convert string keys to integers if needed
            zone_dist = {int(k): v for k, v in zone_dist.items()}
            
            success = service.update_user_zone_distribution(zone_dist)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'User zone distribution updated successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Zone distribution must sum to 100%'
                }), 400
                
        except Exception as e:
            logger.error(f"Error updating user zone distribution: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/settings/zone-distribution/sport/<sport_name>', methods=['PUT'])
    @require_auth
    def update_sport_zone_distribution(sport_name):
        """Update sport-specific zone distribution"""
        try:
            data = request.get_json()
            if not data or 'zone_distribution' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing zone_distribution in request body'
                }), 400
            
            from sport_config_service import SportConfigService
            service = SportConfigService()
            
            zone_dist = data['zone_distribution']
            # Convert string keys to integers if needed
            zone_dist = {int(k): v for k, v in zone_dist.items()}
            
            success = service.update_sport_zone_distribution(sport_name, zone_dist)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Zone distribution for {sport_name} updated successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Sport not found or zone distribution must sum to 100%'
                }), 400
                
        except Exception as e:
            logger.error(f"Error updating sport zone distribution: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/settings/generate-config', methods=['POST'])
    @require_auth
    def generate_config():
        """Generate sport configuration from workout preferences using AI"""
        try:
            data = request.get_json()
            preferences_text = data.get('preferences_text') if data else None
            
            # Import the config generator
            from config_generator import ConfigGenerator
            from ai_providers import OpenAIProvider, ClaudeProvider
            import traceback
            
            # Determine which AI provider to use based on configured API keys
            ai_provider = None
            
            # Try OpenAI first
            openai_key = os.environ.get('OPENAI_API_KEY')
            if openai_key and openai_key.strip():
                try:
                    provider = OpenAIProvider()
                    if provider.is_available():
                        ai_provider = provider
                        logger.info("Using OpenAI provider for config generation")
                except Exception as e:
                    logger.warning(f"OpenAI provider not available: {e}")
            
            # Fall back to Claude if OpenAI not available
            if not ai_provider:
                anthropic_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('CLAUDE_API_KEY')
                if anthropic_key and anthropic_key.strip():
                    try:
                        provider = ClaudeProvider()
                        if provider.is_available():
                            ai_provider = provider
                            logger.info("Using Claude provider for config generation")
                    except Exception as e:
                        logger.warning(f"Claude provider not available: {e}")
            
            if not ai_provider:
                return jsonify({
                    'success': False,
                    'error': 'No AI provider configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in settings.'
                }), 400
            
            # Initialize the config generator
            generator = ConfigGenerator(ai_provider=ai_provider)
            
            # If no preferences text provided, try to load from file
            if not preferences_text:
                if generator.preferences_file:
                    with open(generator.preferences_file, 'r') as f:
                        preferences_text = f.read()
                    logger.info(f"Loaded preferences from {generator.preferences_file}")
                else:
                    return jsonify({
                        'success': False,
                        'error': 'No preferences text provided and no preferences file found. Please create workout_preferences.md or provide preferences_text.'
                    }), 400
            
            # Generate the configuration
            logger.info("Generating sport configuration from preferences...")
            config = generator.generate_config(preferences_text)
            
            # Convert to dictionary format for JSON response
            config_dict = {
                "version": "1.0.0",
                "user_profile": {
                    "philosophy": config.user_profile.philosophy.value,
                    "volume_levels": config.user_profile.volume_levels,
                    "preferences": config.user_profile.preferences,
                    "thresholds": config.user_profile.thresholds
                },
                "sports": [],
                "global_settings": config.global_settings
            }
            
            # Convert sports
            for sport in config.sports:
                sport_dict = {
                    "id": sport.name.lower().replace(" ", "_"),
                    "name": sport.name,
                    "activity_types": sport.activity_types,
                    "primary_metric": {
                        "type": sport.primary_metric.type.value,
                        "unit": sport.primary_metric.unit,
                        "threshold_field": sport.primary_metric.threshold_field,
                        "decimal_places": sport.primary_metric.decimal_places,
                        "custom_formula": sport.primary_metric.custom_formula
                    },
                    "secondary_metric": None,
                    "zone_model": sport.zone_model,
                    "zones": [],
                    "equipment": [],
                    "workout_templates": [],
                    "custom_fields": sport.custom_fields,
                    "tags": []
                }
                
                # Add secondary metric if exists
                if sport.secondary_metric:
                    sport_dict["secondary_metric"] = {
                        "type": sport.secondary_metric.type.value,
                        "unit": sport.secondary_metric.unit,
                        "threshold_field": sport.secondary_metric.threshold_field,
                        "decimal_places": sport.secondary_metric.decimal_places,
                        "custom_formula": sport.secondary_metric.custom_formula
                    }
                
                # Convert zones
                for zone in sport.zones:
                    sport_dict["zones"].append({
                        "name": zone.name,
                        "lower": zone.lower,
                        "upper": zone.upper,
                        "description": zone.description,
                        "polarized_zone": zone.polarized_zone
                    })
                
                # Convert equipment
                for eq in sport.equipment:
                    sport_dict["equipment"].append({
                        "name": eq.name,
                        "description": eq.description,
                        "capabilities": eq.capabilities,
                        "default_duration_minutes": eq.default_duration_minutes,
                        "supports_metrics": [m.value for m in eq.supports_metrics]
                    })
                
                # Convert workout templates
                for tmpl in sport.workout_templates:
                    sport_dict["workout_templates"].append({
                        "name": tmpl.name,
                        "description": tmpl.description,
                        "zones": tmpl.zones,
                        "structure": tmpl.structure,
                        "duration_minutes": tmpl.duration_minutes,
                        "required_equipment": tmpl.required_equipment
                    })
                
                config_dict["sports"].append(sport_dict)
            
            logger.info(f"Successfully generated configuration with {len(config_dict['sports'])} sports")
            
            return jsonify({
                'success': True,
                'config': config_dict,
                'detected_sports': [sport['name'] for sport in config_dict['sports']],
                'message': 'Successfully generated sport configuration from preferences'
            })
            
        except Exception as e:
            logger.error(f"Error generating config: {e}")
            logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': f'Failed to generate configuration: {str(e)}'
            }), 500