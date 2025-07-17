#!/usr/bin/env python3
"""
Sport Configuration Service

Manages sport configurations, provides zone calculations, and handles
configuration updates. This is the main interface for the rest of the
application to interact with the sport configuration system.
"""

import os
import json
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from datetime import datetime
import logging

from sport_config import (
    TrainingConfig, SportConfig, UserProfile, ZoneDefinition,
    Equipment, WorkoutTemplate, Metric, MetricType, TrainingPhilosophy,
    ConfigValidator, ConfigLoader, create_default_config
)
from logging_config import get_logger, DataValidationError, ConfigurationError

logger = get_logger(__name__)


class ZoneCalculationStrategy:
    """Base class for zone calculation strategies"""
    
    def calculate(self, zone: ZoneDefinition, threshold: float) -> Tuple[float, float]:
        """Calculate zone boundaries based on threshold value"""
        raise NotImplementedError


class PercentageZoneStrategy(ZoneCalculationStrategy):
    """Calculate zones as percentage of threshold"""
    
    def calculate(self, zone: ZoneDefinition, threshold: float) -> Tuple[float, float]:
        lower = float(zone.lower) * threshold / 100 if isinstance(zone.lower, (int, float)) else 0
        upper = float(zone.upper) * threshold / 100 if isinstance(zone.upper, (int, float)) else float('inf')
        return (lower, upper)


class FormulaZoneStrategy(ZoneCalculationStrategy):
    """Calculate zones using formulas (e.g., 'LTHR-30')"""
    
    def calculate(self, zone: ZoneDefinition, threshold: float) -> Tuple[float, float]:
        lower = self._evaluate_formula(zone.lower, threshold)
        upper = self._evaluate_formula(zone.upper, threshold)
        return (lower, upper)
    
    def _evaluate_formula(self, formula: Union[str, float], threshold: float) -> float:
        if isinstance(formula, (int, float)):
            return float(formula)
        
        # Simple formula evaluation (e.g., "LTHR-30", "FTP+10")
        if isinstance(formula, str):
            formula = formula.upper()
            # Replace threshold placeholders
            formula = formula.replace("LTHR", str(threshold))
            formula = formula.replace("FTP", str(threshold))
            formula = formula.replace("THRESHOLD", str(threshold))
            
            try:
                # Safe evaluation of simple arithmetic
                return eval(formula, {"__builtins__": {}}, {})
            except (SyntaxError, NameError, TypeError, ValueError, ZeroDivisionError) as e:
                logger.error(f"Error evaluating formula '{formula}': {e}")
                return 0
        
        return 0


class AbsoluteZoneStrategy(ZoneCalculationStrategy):
    """Use absolute values for zones"""
    
    def calculate(self, zone: ZoneDefinition, threshold: float) -> Tuple[float, float]:
        lower = float(zone.lower) if isinstance(zone.lower, (int, float)) else 0
        upper = float(zone.upper) if isinstance(zone.upper, (int, float)) else float('inf')
        return (lower, upper)


class SportConfigService:
    """Main service for managing sport configurations"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "sport_config.json"
        self.config: TrainingConfig = None
        self.validator = ConfigValidator()
        self._zone_strategies = {
            "percentage": PercentageZoneStrategy(),
            "formula": FormulaZoneStrategy(),
            "absolute": AbsoluteZoneStrategy()
        }
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or create default"""
        if os.path.exists(self.config_path):
            try:
                self.config = ConfigLoader.from_file(self.config_path)
                if not self.validator.validate_config(self.config):
                    print(f"Configuration validation failed, using default config")
                    self.config = create_default_config()
            except Exception as e:
                print(f"Error loading config: {e}, using default")
                self.config = create_default_config()
        else:
            print("No configuration file found, creating default")
            self.config = create_default_config()
            self.save_config()
    
    def save_config(self):
        """Save current configuration to file"""
        config_dict = self.validator._config_to_dict(self.config)
        with open(self.config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    def get_sport_by_activity_type(self, activity_type: str) -> Optional[SportConfig]:
        """Get sport configuration by Strava activity type"""
        for sport in self.config.sports:
            if activity_type in sport.activity_types:
                return sport
        return None
    
    def get_sport_by_name(self, name: str) -> Optional[SportConfig]:
        """Get sport configuration by name"""
        for sport in self.config.sports:
            if sport.name.lower() == name.lower():
                return sport
        return None
    
    def get_all_sports(self) -> List[SportConfig]:
        """Get all configured sports"""
        return self.config.sports
    
    def calculate_zones(self, sport: SportConfig, metric_type: MetricType, 
                       threshold_value: float) -> List[Tuple[str, float, float, int]]:
        """
        Calculate zone boundaries for a sport and metric
        Returns: List of (zone_name, lower, upper, polarized_zone)
        """
        # Get the appropriate zone calculation strategy
        strategy = self._zone_strategies.get(sport.zone_model, self._zone_strategies["percentage"])
        
        zones = []
        for zone in sport.zones:
            lower, upper = strategy.calculate(zone, threshold_value)
            zones.append((zone.name, lower, upper, zone.polarized_zone))
        
        return zones
    
    def get_polarized_zone(self, sport: SportConfig, metric_type: MetricType,
                          value: float, threshold_value: float) -> int:
        """Get polarized zone (1, 2, or 3) for a given metric value"""
        zones = self.calculate_zones(sport, metric_type, threshold_value)
        
        for zone_name, lower, upper, polarized_zone in zones:
            if lower <= value <= upper:
                return polarized_zone
        
        # Default to zone 1 if not found
        return 1
    
    def get_threshold_value(self, sport: SportConfig, metric_type: MetricType) -> Optional[float]:
        """Get threshold value for a metric from user profile"""
        if not self.config.user_profile:
            return None
        
        # Determine which metric to use
        metric = None
        if sport.primary_metric.type == metric_type:
            metric = sport.primary_metric
        elif sport.secondary_metric and sport.secondary_metric.type == metric_type:
            metric = sport.secondary_metric
        
        if not metric:
            return None
        
        # Get threshold from user profile
        return self.config.user_profile.thresholds.get(metric.threshold_field)
    
    def update_threshold(self, threshold_field: str, value: float):
        """Update a threshold value in user profile"""
        if not self.config.user_profile:
            self.config.user_profile = UserProfile(
                philosophy=TrainingPhilosophy.POLARIZED,
                volume_levels={"low": 5, "medium": 10, "high": 15}
            )
        
        self.config.user_profile.thresholds[threshold_field] = value
        self.save_config()
    
    def get_equipment_for_sport(self, sport: SportConfig) -> List[Equipment]:
        """Get available equipment for a sport"""
        return sport.equipment
    
    def get_workout_templates(self, sport: SportConfig, 
                            equipment: Optional[List[str]] = None) -> List[WorkoutTemplate]:
        """Get workout templates, optionally filtered by equipment"""
        templates = sport.workout_templates
        
        if equipment:
            # Filter templates by required equipment
            templates = [t for t in templates 
                        if all(req in equipment for req in t.required_equipment)]
        
        return templates
    
    def add_sport(self, sport: SportConfig) -> bool:
        """Add a new sport configuration"""
        # Check for duplicate activity types
        existing_types = set()
        for s in self.config.sports:
            existing_types.update(s.activity_types)
        
        new_types = set(sport.activity_types)
        if existing_types.intersection(new_types):
            print(f"Activity types {existing_types.intersection(new_types)} already configured")
            return False
        
        self.config.sports.append(sport)
        self.save_config()
        return True
    
    def remove_sport(self, sport_name: str) -> bool:
        """Remove a sport configuration"""
        original_count = len(self.config.sports)
        self.config.sports = [s for s in self.config.sports if s.name != sport_name]
        
        if len(self.config.sports) < original_count:
            self.save_config()
            return True
        return False
    
    def get_training_philosophy(self) -> TrainingPhilosophy:
        """Get user's training philosophy"""
        if self.config.user_profile:
            return self.config.user_profile.philosophy
        return TrainingPhilosophy.POLARIZED
    
    def set_training_philosophy(self, philosophy: TrainingPhilosophy):
        """Set user's training philosophy"""
        if not self.config.user_profile:
            self.config.user_profile = UserProfile(
                philosophy=philosophy,
                volume_levels={"low": 5, "medium": 10, "high": 15}
            )
        else:
            self.config.user_profile.philosophy = philosophy
        self.save_config()
    
    def get_metric_info(self, sport: SportConfig, metric_type: MetricType) -> Optional[Metric]:
        """Get metric information for a sport"""
        if sport.primary_metric.type == metric_type:
            return sport.primary_metric
        elif sport.secondary_metric and sport.secondary_metric.type == metric_type:
            return sport.secondary_metric
        return None
    
    def get_supported_metrics(self, sport: SportConfig) -> List[MetricType]:
        """Get all supported metrics for a sport"""
        metrics = [sport.primary_metric.type]
        if sport.secondary_metric:
            metrics.append(sport.secondary_metric.type)
        return metrics
    
    def export_config(self, path: str):
        """Export configuration to a file"""
        config_dict = self.validator._config_to_dict(self.config)
        with open(path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    def import_config(self, path: str) -> bool:
        """Import configuration from a file"""
        try:
            new_config = ConfigLoader.from_file(path)
            if self.validator.validate_config(new_config):
                self.config = new_config
                self.save_config()
                return True
            else:
                print("Imported configuration failed validation")
                return False
        except Exception as e:
            print(f"Error importing configuration: {e}")
            return False
    
    def get_zone_distribution_target(self) -> Dict[int, float]:
        """Get target zone distribution based on training philosophy"""
        philosophy = self.get_training_philosophy()
        
        if philosophy == TrainingPhilosophy.POLARIZED:
            return {1: 80.0, 2: 10.0, 3: 10.0}
        elif philosophy == TrainingPhilosophy.PYRAMIDAL:
            return {1: 70.0, 2: 20.0, 3: 10.0}
        elif philosophy == TrainingPhilosophy.THRESHOLD:
            return {1: 60.0, 2: 30.0, 3: 10.0}
        else:
            # Custom - get from user preferences
            if self.config.user_profile and "zone_distribution" in self.config.user_profile.preferences:
                return self.config.user_profile.preferences["zone_distribution"]
            return {1: 80.0, 2: 10.0, 3: 10.0}  # Default to polarized
    
    def update_sport_zones(self, sport_name: str, zones: List[ZoneDefinition]):
        """Update zones for a sport"""
        sport = self.get_sport_by_name(sport_name)
        if sport:
            sport.zones = zones
            self.save_config()
            return True
        return False
    
    def get_activity_type_mapping(self) -> Dict[str, str]:
        """Get mapping of all activity types to sport names"""
        mapping = {}
        for sport in self.config.sports:
            for activity_type in sport.activity_types:
                mapping[activity_type] = sport.name
        return mapping