#!/usr/bin/env python3
"""
AI-Powered Configuration Generator

Generates structured sport configuration from natural language preferences
in workout_preferences_personal.md or workout_preferences.md files.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

from sport_config import (
    TrainingConfig, SportConfig, UserProfile, ZoneDefinition,
    Equipment, WorkoutTemplate, Metric, MetricType, TrainingPhilosophy,
    ZoneModelType
)
from ai_providers import AIProvider, OpenAIProvider, ClaudeProvider


class ConfigGenerator:
    """Generates sport configuration using AI from natural language preferences"""
    
    def __init__(self, ai_provider: Optional[AIProvider] = None):
        self.ai_provider = ai_provider or self._get_default_provider()
        self.preferences_file = self._find_preferences_file()
    
    def _get_default_provider(self) -> AIProvider:
        """Get the first available AI provider"""
        providers = [OpenAIProvider(), ClaudeProvider()]
        for provider in providers:
            if provider.is_available():
                return provider
        raise RuntimeError("No AI provider available. Please configure OPENAI_API_KEY or ANTHROPIC_API_KEY")
    
    def _find_preferences_file(self) -> Optional[str]:
        """Find the user's workout preferences file"""
        # Priority: personal file first, then default
        files = ["workout_preferences_personal.md", "workout_preferences.md"]
        for file in files:
            if os.path.exists(file):
                return file
        return None
    
    def generate_config(self, preferences_text: Optional[str] = None) -> TrainingConfig:
        """Generate a complete training configuration from preferences"""
        if not preferences_text and self.preferences_file:
            with open(self.preferences_file, 'r') as f:
                preferences_text = f.read()
        
        if not preferences_text:
            raise ValueError("No preferences text provided and no preferences file found")
        
        # Generate configuration using AI
        config_json = self._generate_config_json(preferences_text)
        
        # Parse and validate the generated configuration
        try:
            config_dict = json.loads(config_json)
            return self._dict_to_config(config_dict)
        except json.JSONDecodeError as e:
            print(f"Error parsing generated configuration: {e}")
            # Fall back to a basic configuration based on detected sports
            return self._generate_fallback_config(preferences_text)
    
    def _generate_config_json(self, preferences_text: str) -> str:
        """Use AI to generate configuration JSON from preferences"""
        prompt = f"""
You are an expert in training analysis and sport science. Based on the following workout preferences, 
generate a complete sport configuration in JSON format that follows this structure:

{{
    "version": "1.0.0",
    "user_profile": {{
        "philosophy": "polarized|pyramidal|threshold|custom",
        "volume_levels": {{"low": hours_per_week, "medium": hours_per_week, "high": hours_per_week}},
        "thresholds": {{"ftp": value, "lthr": value, ...}},
        "preferences": {{
            "zone_distribution": {{"1": 80, "2": 10, "3": 10}}  // Zone percentages
        }}
    "sports": [
        {{
            "name": "Sport Name",
            "activity_types": ["Strava activity types"],
            "primary_metric": {{
                "type": "power|heart_rate|pace|speed",
                "unit": "watts|bpm|min/km|km/h",
                "threshold_field": "ftp|lthr|threshold_pace",
                "decimal_places": 0
            }},
            "secondary_metric": {{...}} or null,
            "zone_model": "percentage|formula|absolute",
            "zones": [
                {{
                    "name": "Zone Name",
                    "lower": numeric_value_or_percentage,
                    "upper": numeric_value_or_percentage,
                    "description": "Zone description",
                    "polarized_zone": 1|2|3
                }}
            ],
            "equipment": [
                {{
                    "name": "Equipment Name",
                    "description": "Description",
                    "capabilities": ["capability1", "capability2"],
                    "default_duration_minutes": null or number,
                    "supports_metrics": ["power", "heart_rate"]
                }}
            ],
            "workout_templates": [
                {{
                    "name": "Template Name",
                    "description": "Description",
                    "zones": [zone_numbers],
                    "structure": "Workout structure description",
                    "duration_minutes": null or number,
                    "required_equipment": ["equipment_names"]
                }}
            ]
        }}
    ]
}}

Important guidelines:
1. Detect all sports mentioned in the preferences (cycling, running, rowing, swimming, etc.)
2. Map activity types correctly (e.g., "Ride" and "VirtualRide" for cycling)
3. Choose appropriate metrics for each sport (power for cycling, heart rate for running)
4. Create zones that map to a 3-zone polarized model (Zone 1: 80%, Zone 2: 10%, Zone 3: 10%)
5. Include any equipment mentioned (Peloton, Concept2, etc.)
6. Extract threshold values if mentioned (FTP, LTHR, etc.)
7. Detect training philosophy from the preferences
8. For zones, use percentage model by default unless specific values are given
9. Extract zone distribution preferences if mentioned (e.g., "80/10/10", "polarized distribution", "Zone 1: 80%", etc.)
   - Default to 80/10/10 for polarized, 70/20/10 for pyramidal, 50/35/15 for threshold
   - Look for phrases like "zone distribution", "training distribution", "zone percentages"
   - Parse formats like "80/10/10", "Zone 1: 80%, Zone 2: 10%, Zone 3: 10%", etc.

User's workout preferences:
{preferences_text}

Generate the complete JSON configuration:
"""
        
        response = self.ai_provider.generate_completion(prompt, temperature=0.3)
        
        # Extract JSON from the response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json_match.group(0)
        return response
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> TrainingConfig:
        """Convert dictionary to TrainingConfig object"""
        config = TrainingConfig(version=config_dict.get("version", "1.0"))
        
        # Parse user profile
        if "user_profile" in config_dict:
            profile_dict = config_dict["user_profile"]
            config.user_profile = UserProfile(
                philosophy=TrainingPhilosophy(profile_dict.get("philosophy", "polarized")),
                volume_levels=profile_dict.get("volume_levels", {"low": 5, "medium": 10, "high": 15}),
                preferences=profile_dict.get("preferences", {}),
                thresholds=profile_dict.get("thresholds", {})
            )
        
        # Parse sports
        for sport_dict in config_dict.get("sports", []):
            sport = self._parse_sport(sport_dict)
            config.sports.append(sport)
        
        config.global_settings = config_dict.get("global_settings", {})
        return config
    
    def _parse_sport(self, sport_dict: Dict[str, Any]) -> SportConfig:
        """Parse a sport configuration from dictionary"""
        # Parse metrics
        primary_metric = self._parse_metric(sport_dict["primary_metric"])
        secondary_metric = None
        if sport_dict.get("secondary_metric"):
            secondary_metric = self._parse_metric(sport_dict["secondary_metric"])
        
        sport = SportConfig(
            name=sport_dict["name"],
            activity_types=sport_dict["activity_types"],
            primary_metric=primary_metric,
            secondary_metric=secondary_metric,
            zone_model=sport_dict.get("zone_model", "percentage"),
            custom_fields=sport_dict.get("custom_fields", {})
        )
        
        # Parse zones
        for zone_dict in sport_dict.get("zones", []):
            zone = ZoneDefinition(
                name=zone_dict["name"],
                lower=zone_dict["lower"],
                upper=zone_dict["upper"],
                description=zone_dict.get("description", ""),
                polarized_zone=zone_dict.get("polarized_zone", 1)
            )
            sport.zones.append(zone)
        
        # Parse equipment
        for eq_dict in sport_dict.get("equipment", []):
            equipment = Equipment(
                name=eq_dict["name"],
                description=eq_dict.get("description", ""),
                capabilities=eq_dict.get("capabilities", []),
                default_duration_minutes=eq_dict.get("default_duration_minutes"),
                supports_metrics=[MetricType(m) for m in eq_dict.get("supports_metrics", [])]
            )
            sport.equipment.append(equipment)
        
        # Parse workout templates
        for tmpl_dict in sport_dict.get("workout_templates", []):
            template = WorkoutTemplate(
                name=tmpl_dict["name"],
                description=tmpl_dict.get("description", ""),
                zones=tmpl_dict["zones"],
                structure=tmpl_dict.get("structure", ""),
                duration_minutes=tmpl_dict.get("duration_minutes"),
                required_equipment=tmpl_dict.get("required_equipment", [])
            )
            sport.workout_templates.append(template)
        
        return sport
    
    def _parse_metric(self, metric_dict: Dict[str, Any]) -> Metric:
        """Parse a metric configuration from dictionary"""
        return Metric(
            type=MetricType(metric_dict["type"]),
            unit=metric_dict["unit"],
            threshold_field=metric_dict["threshold_field"],
            decimal_places=metric_dict.get("decimal_places", 0),
            custom_formula=metric_dict.get("custom_formula")
        )
    
    def _generate_fallback_config(self, preferences_text: str) -> TrainingConfig:
        """Generate a basic configuration when AI parsing fails"""
        config = TrainingConfig()
        
        # Default user profile
        config.user_profile = UserProfile(
            philosophy=TrainingPhilosophy.POLARIZED,
            volume_levels={"low": 5, "medium": 10, "high": 15},
            thresholds={}
        )
        
        # Detect sports from preferences
        sports_to_add = []
        
        # Check for cycling
        if any(word in preferences_text.lower() for word in ["cycling", "bike", "peloton", "ride"]):
            sports_to_add.append(self._create_default_cycling())
        
        # Check for running
        if any(word in preferences_text.lower() for word in ["running", "run", "jog"]):
            sports_to_add.append(self._create_default_running())
        
        # Check for rowing
        if any(word in preferences_text.lower() for word in ["rowing", "row", "concept2", "erg"]):
            sports_to_add.append(self._create_default_rowing())
        
        # Check for swimming
        if any(word in preferences_text.lower() for word in ["swimming", "swim", "pool"]):
            sports_to_add.append(self._create_default_swimming())
        
        # If no sports detected, add cycling and running as defaults
        if not sports_to_add:
            sports_to_add.extend([self._create_default_cycling(), self._create_default_running()])
        
        config.sports = sports_to_add
        
        # Try to extract threshold values
        ftp_match = re.search(r'FTP[:\s]+(\d+)', preferences_text, re.IGNORECASE)
        if ftp_match:
            config.user_profile.thresholds["ftp"] = float(ftp_match.group(1))
        
        lthr_match = re.search(r'LTHR[:\s]+(\d+)', preferences_text, re.IGNORECASE)
        if lthr_match:
            config.user_profile.thresholds["lthr"] = float(lthr_match.group(1))
        
        # Try to extract zone distribution
        zone_dist = self._extract_zone_distribution(preferences_text)
        if zone_dist:
            config.user_profile.preferences["zone_distribution"] = zone_dist
        
        return config
    
    def _extract_zone_distribution(self, text: str) -> Optional[Dict[str, float]]:
        """Extract zone distribution from preferences text"""
        # Check for explicit 80/10/10 format
        pattern1 = re.search(r'(\d+)[/\-](\d+)[/\-](\d+)', text)
        if pattern1:
            z1, z2, z3 = map(float, pattern1.groups())
            if z1 + z2 + z3 == 100:  # Validate percentages
                return {"1": z1, "2": z2, "3": z3}
        
        # Check for zone percentage mentions
        zone_patterns = [
            r'zone\s*1[:\s]+(\d+)%',
            r'zone\s*2[:\s]+(\d+)%',
            r'zone\s*3[:\s]+(\d+)%'
        ]
        zones = {}
        for i, pattern in enumerate(zone_patterns, 1):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                zones[str(i)] = float(match.group(1))
        
        if len(zones) == 3 and sum(zones.values()) == 100:
            return zones
        
        # Check for training philosophy to set defaults
        text_lower = text.lower()
        if 'polarized' in text_lower:
            return {"1": 80.0, "2": 10.0, "3": 10.0}
        elif 'pyramidal' in text_lower:
            return {"1": 70.0, "2": 20.0, "3": 10.0}
        elif 'threshold' in text_lower:
            return {"1": 50.0, "2": 35.0, "3": 15.0}
        
        # Default to polarized if no specific distribution found
        return {"1": 80.0, "2": 10.0, "3": 10.0}
    
    def _create_default_cycling(self) -> SportConfig:
        """Create default cycling configuration"""
        sport = SportConfig(
            name="Cycling",
            activity_types=["Ride", "VirtualRide"],
            primary_metric=Metric(
                type=MetricType.POWER,
                unit="watts",
                threshold_field="ftp"
            ),
            secondary_metric=Metric(
                type=MetricType.HEART_RATE,
                unit="bpm",
                threshold_field="lthr"
            ),
            zone_model="percentage"
        )
        
        # Coggan power zones mapped to 3-zone model
        sport.zones = [
            ZoneDefinition("Recovery", 0, 55, "Easy recovery riding", 1),
            ZoneDefinition("Endurance", 56, 75, "Aerobic endurance", 1),
            ZoneDefinition("Tempo", 76, 90, "Moderate effort", 2),
            ZoneDefinition("Threshold", 91, 105, "Lactate threshold", 2),
            ZoneDefinition("VO2 Max", 106, 120, "Maximum aerobic power", 3),
            ZoneDefinition("Anaerobic", 121, 150, "Short intense efforts", 3)
        ]
        
        return sport
    
    def _create_default_running(self) -> SportConfig:
        """Create default running configuration"""
        sport = SportConfig(
            name="Running",
            activity_types=["Run"],
            primary_metric=Metric(
                type=MetricType.HEART_RATE,
                unit="bpm",
                threshold_field="lthr"
            ),
            zone_model="percentage"
        )
        
        # 5-zone HR model mapped to 3-zone
        sport.zones = [
            ZoneDefinition("Zone 1", 0, 85, "Easy aerobic", 1),
            ZoneDefinition("Zone 2", 85, 89, "Moderate aerobic", 1),
            ZoneDefinition("Zone 3", 90, 94, "Threshold", 2),
            ZoneDefinition("Zone 4", 95, 99, "VO2 Max", 3),
            ZoneDefinition("Zone 5", 100, 110, "Max effort", 3)
        ]
        
        return sport
    
    def _create_default_rowing(self) -> SportConfig:
        """Create default rowing configuration"""
        sport = SportConfig(
            name="Rowing",
            activity_types=["Rowing"],
            primary_metric=Metric(
                type=MetricType.HEART_RATE,
                unit="bpm",
                threshold_field="lthr"
            ),
            zone_model="percentage"
        )
        
        # Similar to running zones
        sport.zones = [
            ZoneDefinition("UT2", 0, 75, "Utilization 2 - Easy aerobic", 1),
            ZoneDefinition("UT1", 75, 85, "Utilization 1 - Moderate aerobic", 1),
            ZoneDefinition("AT", 85, 95, "Anaerobic threshold", 2),
            ZoneDefinition("TR", 95, 100, "Transport - VO2 Max", 3),
            ZoneDefinition("AN", 100, 110, "Anaerobic - Max effort", 3)
        ]
        
        # Add Concept2 equipment
        sport.equipment.append(Equipment(
            name="Concept2",
            description="Concept2 rowing ergometer",
            capabilities=["indoor", "power_meter", "pace_tracking"],
            supports_metrics=[MetricType.HEART_RATE, MetricType.PACE]
        ))
        
        return sport
    
    def _create_default_swimming(self) -> SportConfig:
        """Create default swimming configuration"""
        sport = SportConfig(
            name="Swimming",
            activity_types=["Swim"],
            primary_metric=Metric(
                type=MetricType.PACE,
                unit="min/100m",
                threshold_field="threshold_pace"
            ),
            zone_model="percentage"
        )
        
        # Swimming zones based on CSS (Critical Swim Speed)
        sport.zones = [
            ZoneDefinition("Recovery", 120, 200, "Easy recovery pace", 1),
            ZoneDefinition("Aerobic", 110, 120, "Aerobic endurance", 1),
            ZoneDefinition("Threshold", 100, 110, "CSS pace", 2),
            ZoneDefinition("VO2 Max", 90, 100, "Above CSS", 3),
            ZoneDefinition("Sprint", 0, 90, "Sprint efforts", 3)
        ]
        
        return sport
    
    def update_config_from_preferences(self, existing_config: TrainingConfig, 
                                     preferences_text: Optional[str] = None) -> TrainingConfig:
        """Update an existing configuration based on new preferences"""
        # Generate new configuration
        new_config = self.generate_config(preferences_text)
        
        # Merge with existing configuration
        # Keep existing thresholds if not specified in new preferences
        if existing_config.user_profile and existing_config.user_profile.thresholds:
            for field, value in existing_config.user_profile.thresholds.items():
                if field not in new_config.user_profile.thresholds:
                    new_config.user_profile.thresholds[field] = value
        
        return new_config


def main():
    """Main function to generate configuration from preferences"""
    try:
        generator = ConfigGenerator()
        config = generator.generate_config()
        
        # Convert to dictionary format for JSON
        config_dict = {
            "version": "1.0.0",  # Use proper semantic version
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
        
        # Save to file
        with open("sport_config.json", "w") as f:
            json.dump(config_dict, f, indent=2)
        
        print("Successfully generated sport_config.json from workout preferences!")
        print(f"Detected sports: {[sport['name'] for sport in config_dict['sports']]}")
        
    except Exception as e:
        print(f"Error generating configuration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()