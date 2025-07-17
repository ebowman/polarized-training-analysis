#!/usr/bin/env python3
"""
Zone Calculator Module

Provides a unified interface for all zone calculations in the PolarFlow application.
This module consolidates duplicate zone calculation logic and provides a clean API
for zone percentage calculations, zone mapping, and sport-specific calculations.

Key Features:
- Unified zone calculation logic
- Support for 7-zone to 3-zone (polarized) mapping
- Sport-specific zone calculations
- Strategy pattern for different calculation methods
- Full backward compatibility with existing code
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
import os
from dotenv import load_dotenv

# Import sport configuration if available
try:
    from sport_config_service import SportConfigService
    from sport_config import MetricType
    USE_SPORT_CONFIG = os.getenv('USE_SPORT_CONFIG', 'true').lower() == 'true'
except ImportError:
    USE_SPORT_CONFIG = False
    SportConfigService = None
    MetricType = None

load_dotenv()


class ZoneModel(Enum):
    """Zone model types"""
    PERCENTAGE = "percentage"  # Zones as percentage of threshold
    FORMULA = "formula"       # Zones using formulas (e.g., LTHR-30)
    ABSOLUTE = "absolute"     # Absolute values for zones
    CUSTOM = "custom"        # Custom zone definitions


@dataclass
class ZoneBoundary:
    """Represents a zone boundary with lower and upper limits"""
    lower: float
    upper: float
    name: str
    number: int
    polarized_zone: int  # Maps to 1, 2, or 3 for polarized training


class ZoneCalculationStrategy(ABC):
    """Abstract base class for zone calculation strategies"""
    
    @abstractmethod
    def calculate_zones(self, threshold: float, sport_type: Optional[str] = None) -> List[ZoneBoundary]:
        """Calculate zone boundaries based on threshold value"""
        pass
    
    @abstractmethod
    def get_zone_number(self, value: float, threshold: float, sport_type: Optional[str] = None) -> int:
        """Get zone number for a given value"""
        pass


class HeartRateZoneStrategy(ZoneCalculationStrategy):
    """Heart rate zone calculation strategy (7-zone LTHR model)"""
    
    def calculate_zones(self, threshold: float, sport_type: Optional[str] = None) -> List[ZoneBoundary]:
        """Calculate HR zones based on LTHR"""
        zones = [
            ZoneBoundary(0, threshold * 0.81, "Recovery", 1, 1),           # Z1: <81% LTHR
            ZoneBoundary(threshold * 0.81, threshold * 0.89, "Aerobic", 2, 1),    # Z2: 81-89% LTHR
            ZoneBoundary(threshold * 0.90, threshold * 0.93, "Tempo", 3, 2),      # Z3: 90-93% LTHR
            ZoneBoundary(threshold * 0.94, threshold * 0.99, "Threshold", 4, 2),  # Z4: 94-99% LTHR
            ZoneBoundary(threshold * 1.00, threshold * 1.02, "VO2max", 5, 3),     # Z5a: 100-102% LTHR
            ZoneBoundary(threshold * 1.03, threshold * 1.06, "Anaerobic", 6, 3),  # Z5b: 103-106% LTHR
            ZoneBoundary(threshold * 1.06, float('inf'), "Neuromuscular", 7, 3)   # Z5c: >106% LTHR
        ]
        return zones
    
    def get_zone_number(self, value: float, threshold: float, sport_type: Optional[str] = None) -> int:
        """Get HR zone number for a given heart rate"""
        zones = self.calculate_zones(threshold, sport_type)
        for zone in zones:
            if zone.lower <= value <= zone.upper:
                return zone.number
        return 7  # Default to highest zone


class PowerZoneStrategy(ZoneCalculationStrategy):
    """Power zone calculation strategy (7-zone Coggan model)"""
    
    def calculate_zones(self, threshold: float, sport_type: Optional[str] = None) -> List[ZoneBoundary]:
        """Calculate power zones based on FTP"""
        zones = [
            ZoneBoundary(0, threshold * 0.55, "Recovery", 1, 1),              # Z1: <55% FTP
            ZoneBoundary(threshold * 0.56, threshold * 0.75, "Endurance", 2, 1),     # Z2: 56-75% FTP
            ZoneBoundary(threshold * 0.76, threshold * 0.90, "Tempo", 3, 2),         # Z3: 76-90% FTP
            ZoneBoundary(threshold * 0.91, threshold * 1.05, "Threshold", 4, 2),     # Z4: 91-105% FTP
            ZoneBoundary(threshold * 1.06, threshold * 1.20, "VO2max", 5, 3),        # Z5: 106-120% FTP
            ZoneBoundary(threshold * 1.21, threshold * 1.50, "Anaerobic", 6, 3),     # Z6: 121-150% FTP
            ZoneBoundary(threshold * 1.50, float('inf'), "Neuromuscular", 7, 3)      # Z7: >150% FTP
        ]
        return zones
    
    def get_zone_number(self, value: float, threshold: float, sport_type: Optional[str] = None) -> int:
        """Get power zone number for a given power value"""
        zones = self.calculate_zones(threshold, sport_type)
        for zone in zones:
            if zone.lower <= value <= zone.upper:
                return zone.number
        return 7  # Default to highest zone


class SimpleHeartRateZoneStrategy(ZoneCalculationStrategy):
    """Simple 3-zone model based on max HR (fallback when LTHR not available)"""
    
    def calculate_zones(self, max_hr: float, sport_type: Optional[str] = None) -> List[ZoneBoundary]:
        """Calculate simplified 3-zone model from max HR"""
        zones = [
            ZoneBoundary(0, max_hr * 0.82, "Low", 1, 1),              # Zone 1: <82% max HR
            ZoneBoundary(max_hr * 0.82, max_hr * 0.87, "Threshold", 2, 2),  # Zone 2: 82-87% max HR
            ZoneBoundary(max_hr * 0.87, float('inf'), "High", 3, 3)         # Zone 3: >87% max HR
        ]
        return zones
    
    def get_zone_number(self, value: float, max_hr: float, sport_type: Optional[str] = None) -> int:
        """Get zone number for simplified model"""
        zones = self.calculate_zones(max_hr, sport_type)
        for zone in zones:
            if zone.lower <= value <= zone.upper:
                return zone.number
        return 3  # Default to highest zone


class ZoneCalculator:
    """
    Main zone calculator class that provides a unified interface for all zone calculations.
    
    This class consolidates all zone calculation logic and provides:
    - Zone boundary calculations
    - Zone percentage calculations
    - 7-zone to 3-zone polarized mapping
    - Sport-specific zone calculations
    - Strategy pattern for extensibility
    """
    
    def __init__(self, max_hr: Optional[int] = None, lthr: Optional[int] = None, 
                 ftp: Optional[int] = None):
        """
        Initialize zone calculator with thresholds.
        
        Args:
            max_hr: Maximum heart rate
            lthr: Lactate threshold heart rate
            ftp: Functional threshold power
        """
        # Load from environment if not provided
        self.max_hr = max_hr if max_hr is not None else int(os.getenv("MAX_HEART_RATE", "180"))
        self.lthr = lthr if lthr is not None else int(os.getenv("AVERAGE_FTP_HR", "0"))
        self.ftp = ftp if ftp is not None else int(os.getenv("FTP", "250"))
        
        # Initialize strategies
        self._hr_strategy = HeartRateZoneStrategy()
        self._power_strategy = PowerZoneStrategy()
        self._simple_hr_strategy = SimpleHeartRateZoneStrategy()
        
        # Initialize sport config service if available
        self.sport_config_service = None
        if USE_SPORT_CONFIG and SportConfigService:
            try:
                self.sport_config_service = SportConfigService()
            except Exception as e:
                print(f"Warning: Could not initialize SportConfigService: {e}")
                self.sport_config_service = None
    
    def calculate_hr_zones(self, sport_type: Optional[str] = None) -> List[ZoneBoundary]:
        """
        Calculate heart rate zones.
        
        Args:
            sport_type: Optional sport type for sport-specific calculations
            
        Returns:
            List of ZoneBoundary objects
        """
        # Try sport-specific calculation first
        if self.sport_config_service and sport_type:
            zones = self._calculate_sport_specific_zones(sport_type, MetricType.HEART_RATE)
            if zones:
                return zones
        
        # Use LTHR-based zones if available
        if self.lthr > 0:
            return self._hr_strategy.calculate_zones(self.lthr, sport_type)
        else:
            # Fall back to simple max HR model
            return self._simple_hr_strategy.calculate_zones(self.max_hr, sport_type)
    
    def calculate_power_zones(self, sport_type: Optional[str] = None) -> List[ZoneBoundary]:
        """
        Calculate power zones.
        
        Args:
            sport_type: Optional sport type for sport-specific calculations
            
        Returns:
            List of ZoneBoundary objects
        """
        # Try sport-specific calculation first
        if self.sport_config_service and sport_type:
            zones = self._calculate_sport_specific_zones(sport_type, MetricType.POWER)
            if zones:
                return zones
        
        # Use standard power zones
        return self._power_strategy.calculate_zones(self.ftp, sport_type)
    
    def get_hr_zone(self, hr: int, sport_type: Optional[str] = None) -> int:
        """
        Get heart rate zone number (1-7) for a given heart rate.
        
        Args:
            hr: Heart rate value
            sport_type: Optional sport type for sport-specific calculations
            
        Returns:
            Zone number (1-7)
        """
        # Try sport-specific calculation first
        if self.sport_config_service and sport_type:
            zone = self._get_sport_specific_zone(hr, sport_type, MetricType.HEART_RATE)
            if zone:
                return zone
        
        # Use appropriate strategy
        if self.lthr > 0:
            return self._hr_strategy.get_zone_number(hr, self.lthr, sport_type)
        else:
            return self._simple_hr_strategy.get_zone_number(hr, self.max_hr, sport_type)
    
    def get_power_zone(self, power: int, sport_type: Optional[str] = None) -> int:
        """
        Get power zone number (1-7) for a given power value.
        
        Args:
            power: Power value in watts
            sport_type: Optional sport type for sport-specific calculations
            
        Returns:
            Zone number (1-7)
        """
        # Try sport-specific calculation first
        if self.sport_config_service and sport_type:
            zone = self._get_sport_specific_zone(power, sport_type, MetricType.POWER)
            if zone:
                return zone
        
        return self._power_strategy.get_zone_number(power, self.ftp, sport_type)
    
    def map_to_polarized_zone(self, zone_7: int, metric_type: str = "heart_rate", 
                             sport_type: Optional[str] = None) -> int:
        """
        Map 7-zone model to 3-zone polarized model.
        
        Args:
            zone_7: Zone number in 7-zone model (1-7)
            metric_type: Type of metric ("heart_rate" or "power")
            sport_type: Optional sport type for sport-specific mapping
            
        Returns:
            Polarized zone number (1-3)
        """
        # Try sport-specific mapping first
        if self.sport_config_service and sport_type:
            sport = self.sport_config_service.get_sport_by_activity_type(sport_type)
            if sport and zone_7 <= len(sport.zones):
                return sport.zones[zone_7 - 1].polarized_zone
        
        # Standard mapping
        if zone_7 <= 2:  # Z1-Z2 -> Zone 1 (Low intensity)
            return 1
        elif zone_7 <= 4:  # Z3-Z4 -> Zone 2 (Threshold)
            return 2
        else:  # Z5-Z7 -> Zone 3 (High intensity)
            return 3
    
    def calculate_zone_percentages(self, zone_times: Dict[int, float]) -> Dict[int, float]:
        """
        Calculate zone percentages from zone times.
        
        Args:
            zone_times: Dictionary mapping zone number to time in seconds
            
        Returns:
            Dictionary mapping zone number to percentage
        """
        total_time = sum(zone_times.values())
        if total_time == 0:
            return {zone: 0.0 for zone in zone_times}
        
        return {
            zone: (time / total_time * 100) 
            for zone, time in zone_times.items()
        }
    
    def calculate_polarized_percentages(self, zone_times: Dict[int, float], 
                                       metric_type: str = "heart_rate",
                                       sport_type: Optional[str] = None) -> Dict[int, float]:
        """
        Calculate polarized zone percentages (3-zone model) from 7-zone times.
        
        Args:
            zone_times: Dictionary mapping 7-zone numbers to time in seconds
            metric_type: Type of metric ("heart_rate" or "power")
            sport_type: Optional sport type for sport-specific mapping
            
        Returns:
            Dictionary with keys 1, 2, 3 for polarized zones and their percentages
        """
        # Aggregate times into polarized zones
        polarized_times = {1: 0.0, 2: 0.0, 3: 0.0}
        
        for zone_7, time in zone_times.items():
            polarized_zone = self.map_to_polarized_zone(zone_7, metric_type, sport_type)
            polarized_times[polarized_zone] += time
        
        # Calculate percentages
        return self.calculate_zone_percentages(polarized_times)
    
    def get_zone_distribution_targets(self, philosophy: str = "polarized") -> Dict[int, float]:
        """
        Get target zone distribution percentages based on training philosophy.
        
        Args:
            philosophy: Training philosophy ("polarized", "pyramidal", "threshold")
            
        Returns:
            Dictionary with target percentages for zones 1, 2, 3
        """
        if self.sport_config_service:
            return self.sport_config_service.get_zone_distribution_target()
        
        # Default targets
        targets = {
            "polarized": {1: 80.0, 2: 10.0, 3: 10.0},
            "pyramidal": {1: 70.0, 2: 20.0, 3: 10.0},
            "threshold": {1: 60.0, 2: 30.0, 3: 10.0}
        }
        
        return targets.get(philosophy, targets["polarized"])
    
    def calculate_zone_deviations(self, actual_percentages: Dict[int, float], 
                                 philosophy: str = "polarized") -> Dict[int, float]:
        """
        Calculate deviations from target zone distribution.
        
        Args:
            actual_percentages: Actual zone percentages
            philosophy: Training philosophy
            
        Returns:
            Dictionary with deviations for each zone (positive = excess, negative = deficit)
        """
        targets = self.get_zone_distribution_targets(philosophy)
        
        return {
            zone: actual_percentages.get(zone, 0) - targets.get(zone, 0)
            for zone in [1, 2, 3]
        }
    
    def calculate_adherence_score(self, actual_percentages: Dict[int, float],
                                 philosophy: str = "polarized") -> float:
        """
        Calculate adherence score (0-100) based on deviation from targets.
        
        Args:
            actual_percentages: Actual zone percentages
            philosophy: Training philosophy
            
        Returns:
            Adherence score from 0 to 100
        """
        deviations = self.calculate_zone_deviations(actual_percentages, philosophy)
        
        # Weighted scoring (Zone 1 is most important)
        zone1_weight = 0.5
        zone2_weight = 0.25
        zone3_weight = 0.25
        
        total_deviation = (
            abs(deviations[1]) * zone1_weight +
            abs(deviations[2]) * zone2_weight +
            abs(deviations[3]) * zone3_weight
        )
        
        return max(0, 100 - total_deviation)
    
    def update_thresholds(self, max_hr: Optional[int] = None, lthr: Optional[int] = None,
                         ftp: Optional[int] = None):
        """
        Update threshold values.
        
        Args:
            max_hr: Maximum heart rate
            lthr: Lactate threshold heart rate
            ftp: Functional threshold power
        """
        if max_hr is not None:
            self.max_hr = max_hr
        if lthr is not None:
            self.lthr = lthr
        if ftp is not None:
            self.ftp = ftp
        
        # Update in sport config if available
        if self.sport_config_service:
            if max_hr is not None:
                self.sport_config_service.update_threshold('max_hr', max_hr)
            if lthr is not None:
                self.sport_config_service.update_threshold('lthr', lthr)
            if ftp is not None:
                self.sport_config_service.update_threshold('ftp', ftp)
    
    # Private helper methods
    
    def _calculate_sport_specific_zones(self, sport_type: str, 
                                       metric_type: MetricType) -> Optional[List[ZoneBoundary]]:
        """Calculate zones using sport configuration"""
        if not self.sport_config_service:
            return None
        
        sport = self.sport_config_service.get_sport_by_activity_type(sport_type)
        if not sport:
            return None
        
        threshold = self.sport_config_service.get_threshold_value(sport, metric_type)
        if not threshold:
            return None
        
        zones = self.sport_config_service.calculate_zones(sport, metric_type, threshold)
        
        # Convert to ZoneBoundary objects
        zone_boundaries = []
        for i, (zone_name, lower, upper, polarized_zone) in enumerate(zones, 1):
            zone_boundaries.append(
                ZoneBoundary(lower, upper, zone_name, i, polarized_zone)
            )
        
        return zone_boundaries
    
    def _get_sport_specific_zone(self, value: float, sport_type: str,
                                metric_type: MetricType) -> Optional[int]:
        """Get zone number using sport configuration"""
        if not self.sport_config_service:
            return None
        
        sport = self.sport_config_service.get_sport_by_activity_type(sport_type)
        if not sport:
            return None
        
        threshold = self.sport_config_service.get_threshold_value(sport, metric_type)
        if not threshold:
            return None
        
        zones = self.sport_config_service.calculate_zones(sport, metric_type, threshold)
        
        for i, (zone_name, lower, upper, polarized_zone) in enumerate(zones, 1):
            if lower <= value <= upper:
                return i
        
        return len(zones)  # Default to highest zone


# Convenience functions for backward compatibility

def create_zone_calculator(**kwargs) -> ZoneCalculator:
    """Factory function to create a ZoneCalculator instance"""
    return ZoneCalculator(**kwargs)


def calculate_zone_percentages_from_stream(stream_data: List[float], 
                                         threshold: float,
                                         calculator: Optional[ZoneCalculator] = None,
                                         metric_type: str = "heart_rate",
                                         sport_type: Optional[str] = None) -> Dict[int, float]:
    """
    Calculate zone percentages from a stream of data (HR or power).
    
    Args:
        stream_data: List of HR or power values
        threshold: Threshold value (LTHR or FTP)
        calculator: Optional pre-configured ZoneCalculator
        metric_type: Type of data ("heart_rate" or "power")
        sport_type: Optional sport type
        
    Returns:
        Dictionary with zone percentages
    """
    if not calculator:
        calculator = ZoneCalculator()
    
    # Count time in each zone
    zone_counts = {i: 0 for i in range(1, 8)}
    
    for value in stream_data:
        if metric_type == "heart_rate":
            zone = calculator.get_hr_zone(value, sport_type)
        else:
            zone = calculator.get_power_zone(value, sport_type)
        zone_counts[zone] += 1
    
    # Convert to percentages
    return calculator.calculate_zone_percentages(zone_counts)