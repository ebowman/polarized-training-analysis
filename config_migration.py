#!/usr/bin/env python3
"""
Configuration Migration Utilities

Helps existing users migrate from the hardcoded system to the new
flexible configuration system. Preserves user data and preferences.
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from sport_config import (
    TrainingConfig, SportConfig, UserProfile, TrainingPhilosophy,
    create_default_config
)
from sport_config_service import SportConfigService
from config_generator import ConfigGenerator
from logging_config import get_logger, DataValidationError, ConfigurationError

logger = get_logger(__name__)


class ConfigMigration:
    """Handles migration from old hardcoded system to new configuration system"""
    
    def __init__(self, backup_dir: str = "migration_backups"):
        self.backup_dir = backup_dir
        self.config_service = None
        self.generator = None
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self):
        """Create backup directory if it doesn't exist"""
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def migrate(self, force: bool = False) -> bool:
        """
        Perform migration from old system to new configuration
        
        Args:
            force: Force migration even if config already exists
            
        Returns:
            True if migration successful, False otherwise
        """
        # Check if already migrated
        if os.path.exists("sport_config.json") and not force:
            logger.info("Configuration already exists. Use force=True to re-migrate.")
            return False
        
        print("Starting migration to new configuration system...")
        
        # Step 1: Backup existing data
        self._backup_existing_data()
        
        # Step 2: Analyze existing setup
        existing_data = self._analyze_existing_setup()
        
        # Step 3: Generate configuration
        config = self._generate_migration_config(existing_data)
        
        # Step 4: Save new configuration
        self.config_service = SportConfigService()
        self.config_service.config = config
        self.config_service.save_config()
        
        # Step 5: Create migration report
        self._create_migration_report(existing_data, config)
        
        print("Migration completed successfully!")
        print(f"Backups saved to: {self.backup_dir}")
        print("New configuration saved to: sport_config.json")
        
        return True
    
    def _backup_existing_data(self):
        """Backup existing configuration and data files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir = os.path.join(self.backup_dir, f"backup_{timestamp}")
        os.makedirs(backup_subdir, exist_ok=True)
        
        # Files to backup
        files_to_backup = [
            ".env",
            "workout_preferences.md",
            "workout_preferences_personal.md",
            "cache/",
            "training_analysis_results.json"
        ]
        
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    dest = os.path.join(backup_subdir, os.path.basename(file_path))
                    shutil.copytree(file_path, dest)
                else:
                    shutil.copy2(file_path, backup_subdir)
                print(f"Backed up: {file_path}")
    
    def _analyze_existing_setup(self) -> Dict[str, Any]:
        """Analyze existing setup to extract configuration data"""
        data = {
            "thresholds": {},
            "sports_used": set(),
            "equipment": set(),
            "preferences_file": None,
            "env_vars": {}
        }
        
        # Check for workout preferences
        if os.path.exists("workout_preferences_personal.md"):
            data["preferences_file"] = "workout_preferences_personal.md"
        elif os.path.exists("workout_preferences.md"):
            data["preferences_file"] = "workout_preferences.md"
        
        # Extract thresholds from .env
        if os.path.exists(".env"):
            with open(".env", 'r') as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        data["env_vars"][key] = value
                        
                        # Extract FTP/LTHR if stored in env
                        if key.upper() == "FTP":
                            try:
                                data["thresholds"]["ftp"] = float(value)
                            except ValueError as e:
                                logger.warning(f"Failed to parse heart rate value for {key}: {e}")
                        elif key.upper() == "LTHR":
                            try:
                                data["thresholds"]["lthr"] = float(value)
                            except ValueError as e:
                                logger.warning(f"Failed to parse heart rate value for {key}: {e}")
        
        # Analyze cached activities to detect sports used
        if os.path.exists("cache"):
            for file in os.listdir("cache"):
                if file.endswith("_activities.json"):
                    sport = file.replace("_activities.json", "")
                    data["sports_used"].add(sport)
        
        # Check for specific equipment mentions in preferences
        if data["preferences_file"]:
            with open(data["preferences_file"], 'r') as f:
                content = f.read().lower()
                if "peloton" in content:
                    data["equipment"].add("Peloton")
                if "concept2" in content or "erg" in content:
                    data["equipment"].add("Concept2")
                if "zwift" in content:
                    data["equipment"].add("Zwift")
        
        # Try to extract thresholds from analysis results
        if os.path.exists("training_analysis_results.json"):
            try:
                with open("training_analysis_results.json", 'r') as f:
                    results = json.load(f)
                    # Look for threshold values in results
                    # This would need to be adapted based on actual structure
            except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                logger.debug(f"Could not parse training analysis results: {e}")
        
        return data
    
    def _generate_migration_config(self, existing_data: Dict[str, Any]) -> TrainingConfig:
        """Generate configuration based on existing setup"""
        # Try AI generation first if preferences file exists
        if existing_data["preferences_file"]:
            try:
                self.generator = ConfigGenerator()
                config = self.generator.generate_config()
                
                # Merge with detected thresholds
                if config.user_profile and existing_data["thresholds"]:
                    config.user_profile.thresholds.update(existing_data["thresholds"])
                
                return config
            except Exception as e:
                print(f"AI generation failed: {e}, using fallback")
        
        # Fallback to manual configuration
        config = create_default_config()
        
        # Update with detected data
        if existing_data["thresholds"]:
            config.user_profile.thresholds.update(existing_data["thresholds"])
        
        # Add equipment if detected
        for sport in config.sports:
            if sport.name == "Cycling" and "Peloton" in existing_data["equipment"]:
                from sport_config import Equipment, MetricType
                sport.equipment.append(Equipment(
                    name="Peloton",
                    description="Peloton bike with power meter",
                    capabilities=["power_meter", "cadence", "heart_rate"],
                    supports_metrics=[MetricType.POWER, MetricType.HEART_RATE]
                ))
            elif sport.name == "Rowing" and "Concept2" in existing_data["equipment"]:
                from sport_config import Equipment, MetricType
                sport.equipment.append(Equipment(
                    name="Concept2",
                    description="Concept2 rowing ergometer",
                    capabilities=["power_meter", "pace", "heart_rate"],
                    supports_metrics=[MetricType.HEART_RATE, MetricType.PACE]
                ))
        
        return config
    
    def _create_migration_report(self, existing_data: Dict[str, Any], 
                                config: TrainingConfig):
        """Create a report of the migration process"""
        report = {
            "migration_date": datetime.now().isoformat(),
            "existing_data_found": existing_data,
            "generated_config": {
                "sports": [sport.name for sport in config.sports],
                "thresholds": config.user_profile.thresholds if config.user_profile else {},
                "philosophy": config.user_profile.philosophy.value if config.user_profile else "polarized"
            },
            "recommendations": []
        }
        
        # Add recommendations
        if not existing_data["thresholds"]:
            report["recommendations"].append(
                "No threshold values found. Please update FTP/LTHR in the configuration."
            )
        
        if not existing_data["preferences_file"]:
            report["recommendations"].append(
                "No workout preferences file found. Consider creating workout_preferences_personal.md"
            )
        
        # Save report
        report_path = os.path.join(self.backup_dir, "migration_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nMigration report saved to: {report_path}")
    
    def rollback(self, backup_timestamp: str):
        """Rollback to a previous backup"""
        backup_dir = os.path.join(self.backup_dir, f"backup_{backup_timestamp}")
        
        if not os.path.exists(backup_dir):
            print(f"Backup not found: {backup_dir}")
            return False
        
        print(f"Rolling back to backup: {backup_timestamp}")
        
        # Remove new config
        if os.path.exists("sport_config.json"):
            os.remove("sport_config.json")
        
        # Restore backed up files
        for item in os.listdir(backup_dir):
            src = os.path.join(backup_dir, item)
            dst = item
            
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            
            print(f"Restored: {item}")
        
        print("Rollback completed successfully!")
        return True
    
    def verify_migration(self) -> bool:
        """Verify that migration was successful"""
        issues = []
        
        # Check config exists and is valid
        if not os.path.exists("sport_config.json"):
            issues.append("Configuration file not found")
        else:
            try:
                service = SportConfigService()
                if not service.config.sports:
                    issues.append("No sports configured")
            except Exception as e:
                issues.append(f"Config loading error: {e}")
        
        # Check for data loss
        if os.path.exists("cache"):
            cache_files = os.listdir("cache")
            if not cache_files:
                issues.append("Cache directory is empty")
        
        if issues:
            print("Migration verification failed:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("Migration verified successfully!")
            return True


class FeatureFlagManager:
    """Manages feature flags for gradual migration"""
    
    def __init__(self, flags_file: str = "feature_flags.json"):
        self.flags_file = flags_file
        self.flags = self._load_flags()
    
    def _load_flags(self) -> Dict[str, bool]:
        """Load feature flags from file"""
        if os.path.exists(self.flags_file):
            with open(self.flags_file, 'r') as f:
                return json.load(f)
        
        # Default flags
        return {
            "use_new_config": False,
            "use_dynamic_zones": False,
            "use_ai_config_gen": True,
            "use_equipment_registry": False,
            "show_config_ui": False
        }
    
    def save_flags(self):
        """Save feature flags to file"""
        with open(self.flags_file, 'w') as f:
            json.dump(self.flags, f, indent=2)
    
    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        return self.flags.get(flag_name, False)
    
    def enable(self, flag_name: str):
        """Enable a feature flag"""
        self.flags[flag_name] = True
        self.save_flags()
    
    def disable(self, flag_name: str):
        """Disable a feature flag"""
        self.flags[flag_name] = False
        self.save_flags()
    
    def toggle(self, flag_name: str):
        """Toggle a feature flag"""
        self.flags[flag_name] = not self.flags.get(flag_name, False)
        self.save_flags()
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags"""
        return self.flags.copy()


def run_migration(force: bool = False):
    """Run the migration process"""
    migration = ConfigMigration()
    success = migration.migrate(force=force)
    
    if success:
        migration.verify_migration()
        
        # Enable feature flags for new system
        flags = FeatureFlagManager()
        flags.enable("use_new_config")
        flags.enable("use_dynamic_zones")
        print("\nFeature flags enabled for new configuration system")
    
    return success


if __name__ == "__main__":
    import sys
    
    force = "--force" in sys.argv
    run_migration(force=force)