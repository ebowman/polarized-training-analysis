#!/usr/bin/env python3
"""
ConfigManager Demonstration Script

This script demonstrates the unified ConfigManager functionality
and shows how it integrates with the existing PolarFlow application.
"""

import os
import sys
from pathlib import Path
import json

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import (
    ConfigManager, get_config_manager, get_config, 
    reload_config, validate_config
)


def demonstrate_priority_resolution():
    """Demonstrate how configuration priority resolution works"""
    print("=== Configuration Priority Resolution Demo ===\n")
    
    config = ConfigManager()
    
    # Show current FTP value and its source
    ftp_cv = config.get_with_metadata('ftp')
    print(f"Current FTP: {ftp_cv.value} watts (from {ftp_cv.source})")
    
    # Show max heart rate value and its source
    max_hr_cv = config.get_with_metadata('max_heart_rate')
    print(f"Max Heart Rate: {max_hr_cv.value} bpm (from {max_hr_cv.source})")
    
    # Show LTHR value and its source
    lthr_cv = config.get_with_metadata('lthr')
    print(f"LTHR: {lthr_cv.value} bpm (from {lthr_cv.source})")
    
    print("\nConfiguration Sources (by priority):")
    for source, values in config.get_all_by_source().items():
        print(f"  {source}: {len(values)} values")
    
    print("\nPriority Resolution Test:")
    print("1. Setting FTP=275 via environment variable...")
    os.environ['FTP'] = '275'
    config.reload()
    
    new_ftp_cv = config.get_with_metadata('ftp')
    print(f"   New FTP: {new_ftp_cv.value} watts (from {new_ftp_cv.source})")
    
    print("2. Setting FTP=285 via runtime...")
    config.set('ftp', 285)
    runtime_ftp_cv = config.get_with_metadata('ftp')
    print(f"   Runtime FTP: {runtime_ftp_cv.value} watts (from {runtime_ftp_cv.source})")
    
    # Clean up
    del os.environ['FTP']
    print("3. Cleaned up environment variable, reloading...")
    config.reload()
    final_ftp_cv = config.get_with_metadata('ftp')
    print(f"   Final FTP: {final_ftp_cv.value} watts (from {final_ftp_cv.source})")


def demonstrate_configuration_sources():
    """Demonstrate different configuration sources"""
    print("\n=== Configuration Sources Demo ===\n")
    
    config = ConfigManager()
    
    # Show environment variables
    print("Environment Variables:")
    env_vars = ['STRAVA_CLIENT_ID', 'STRAVA_CLIENT_SECRET', 'MAX_HEART_RATE', 
                'FTP', 'AVERAGE_FTP_HR', 'AI_PROVIDER', 'OPENAI_API_KEY']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var}: {value}")
        else:
            print(f"  {var}: Not set")
    
    # Show JSON configuration
    print("\nJSON Configuration:")
    if os.path.exists('sport_config.json'):
        with open('sport_config.json', 'r') as f:
            data = json.load(f)
        
        if 'user_profile' in data:
            profile = data['user_profile']
            print(f"  Training Philosophy: {profile.get('philosophy', 'Not set')}")
            print(f"  Volume Levels: {profile.get('volume_levels', 'Not set')}")
            if 'thresholds' in profile:
                print(f"  Thresholds: {profile['thresholds']}")
    else:
        print("  sport_config.json not found")
    
    # Show Markdown preferences
    print("\nMarkdown Preferences:")
    md_files = ['workout_preferences.md', 'workout_preferences_personal.md']
    for md_file in md_files:
        if os.path.exists(md_file):
            print(f"  {md_file}: Found")
            # Show a few lines for context
            with open(md_file, 'r') as f:
                lines = f.readlines()[:5]
                for line in lines:
                    if line.strip():
                        print(f"    {line.strip()}")
        else:
            print(f"  {md_file}: Not found")


def demonstrate_sport_config_integration():
    """Demonstrate sport configuration integration"""
    print("\n=== Sport Configuration Integration Demo ===\n")
    
    config = ConfigManager()
    
    # Test sport config retrieval
    cycling_sport = config.get_sport_config('Cycling')
    if cycling_sport:
        print("Cycling Sport Configuration:")
        print(f"  Name: {cycling_sport.name}")
        print(f"  Activity Types: {cycling_sport.activity_types}")
        print(f"  Primary Metric: {cycling_sport.primary_metric.type.value}")
        print(f"  Zone Model: {cycling_sport.zone_model}")
        print(f"  Number of Zones: {len(cycling_sport.zones)}")
        
        # Show zones
        print("  Zones:")
        for zone in cycling_sport.zones:
            print(f"    {zone.name}: {zone.lower}-{zone.upper}% (Polarized Zone {zone.polarized_zone})")
    else:
        print("Cycling sport configuration not found")
    
    # Test activity type mapping
    print("\nActivity Type Mapping:")
    activity_types = ['Ride', 'Run', 'VirtualRide', 'Swim']
    for activity_type in activity_types:
        sport = config.get_sport_by_activity_type(activity_type)
        if sport:
            print(f"  {activity_type} -> {sport.name}")
        else:
            print(f"  {activity_type} -> No sport configured")


def demonstrate_backward_compatibility():
    """Demonstrate backward compatibility features"""
    print("\n=== Backward Compatibility Demo ===\n")
    
    config = ConfigManager()
    
    # Show that old environment variable names still work
    print("Old Environment Variable Names:")
    old_names = {
        'MAX_HEART_RATE': 'max_heart_rate',
        'AVERAGE_FTP_HR': 'lthr',
        'STRAVA_CLIENT_ID': 'strava_client_id'
    }
    
    for old_name, new_name in old_names.items():
        old_value = os.getenv(old_name)
        new_value = config.get(new_name)
        print(f"  {old_name} -> {new_name}: {old_value} -> {new_value}")
    
    # Show convenient access methods
    print("\nConvenient Access Methods:")
    print(f"  get_config('ftp'): {get_config('ftp')}")
    print(f"  get_config('max_heart_rate'): {get_config('max_heart_rate')}")
    print(f"  get_config('ai_provider'): {get_config('ai_provider')}")


def demonstrate_validation():
    """Demonstrate configuration validation"""
    print("\n=== Configuration Validation Demo ===\n")
    
    config = ConfigManager()
    
    # Validate current configuration
    is_valid, errors = config.validate()
    print(f"Configuration Valid: {is_valid}")
    
    if errors:
        print("Validation Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("No validation errors found")
    
    # Test validation with invalid values
    print("\nTesting Validation with Invalid Values:")
    
    # Set LTHR higher than max heart rate
    original_lthr = config.get('lthr')
    original_max_hr = config.get('max_heart_rate')
    
    config.set('lthr', 200)
    config.set('max_heart_rate', 180)
    
    is_valid, errors = config.validate()
    print(f"After setting LTHR > Max HR: Valid={is_valid}")
    if errors:
        for error in errors:
            print(f"  - {error}")
    
    # Reset values
    config.set('lthr', original_lthr)
    config.set('max_heart_rate', original_max_hr)


def demonstrate_export_import():
    """Demonstrate configuration export/import"""
    print("\n=== Configuration Export/Import Demo ===\n")
    
    config = ConfigManager()
    
    # Export current configuration
    export_file = 'config_export_demo.json'
    config.export_config(export_file, format='json')
    print(f"Configuration exported to {export_file}")
    
    # Show part of exported config
    with open(export_file, 'r') as f:
        data = json.load(f)
    
    print("Exported Configuration Summary:")
    for source, values in data.items():
        print(f"  {source}: {len(values)} values")
    
    # Export as .env format
    env_export_file = 'config_export_demo.env'
    config.export_config(env_export_file, format='env')
    print(f"Configuration exported to {env_export_file}")
    
    # Show part of .env export
    with open(env_export_file, 'r') as f:
        lines = f.readlines()[:10]
    
    print("Sample .env Export:")
    for line in lines:
        if line.strip() and not line.startswith('#'):
            print(f"  {line.strip()}")
    
    # Clean up
    os.unlink(export_file)
    os.unlink(env_export_file)


def demonstrate_migration_compatibility():
    """Demonstrate migration compatibility"""
    print("\n=== Migration Compatibility Demo ===\n")
    
    config = get_config_manager()
    
    # Simulate old code patterns
    print("Simulating Old Code Patterns:")
    
    # Old pattern: os.getenv with defaults
    old_max_hr = os.getenv('MAX_HEART_RATE', '180')
    new_max_hr = config.get('max_heart_rate', 180)
    print(f"  Old: os.getenv('MAX_HEART_RATE', '180') = {old_max_hr}")
    print(f"  New: config.get('max_heart_rate', 180) = {new_max_hr}")
    
    # Old pattern: int conversion
    old_ftp = int(os.getenv('FTP', '250'))
    new_ftp = config.get('ftp', 250)
    print(f"  Old: int(os.getenv('FTP', '250')) = {old_ftp}")
    print(f"  New: config.get('ftp', 250) = {new_ftp}")
    
    # Show that both approaches give same result
    print(f"  Results match: {old_max_hr == str(new_max_hr) and old_ftp == new_ftp}")


def main():
    """Run all demonstrations"""
    print("PolarFlow Unified ConfigManager Demonstration\n")
    print("=" * 50)
    
    try:
        demonstrate_priority_resolution()
        demonstrate_configuration_sources()
        demonstrate_sport_config_integration()
        demonstrate_backward_compatibility()
        demonstrate_validation()
        demonstrate_export_import()
        demonstrate_migration_compatibility()
        
        print("\n" + "=" * 50)
        print("ConfigManager demonstration complete!")
        print("\nNext steps:")
        print("1. Review the generated config_manager.py")
        print("2. Run the migration helper: python config_migration_helper.py")
        print("3. Update your code to use the new ConfigManager")
        print("4. Run tests: pytest tests/test_config_manager.py")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()