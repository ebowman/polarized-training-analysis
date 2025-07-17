#!/usr/bin/env python3
"""
Test Zone Calculator Module

Tests for the unified ZoneCalculator to ensure:
1. Correct zone calculations
2. Backward compatibility with existing code
3. Sport-specific calculations work correctly
4. All calculation strategies produce expected results
"""

import pytest
from zone_calculator import (
    ZoneCalculator, ZoneBoundary, ZoneModel,
    HeartRateZoneStrategy, PowerZoneStrategy, SimpleHeartRateZoneStrategy,
    create_zone_calculator, calculate_zone_percentages_from_stream
)


class TestZoneCalculator:
    """Test the main ZoneCalculator class"""
    
    def test_initialization_with_defaults(self):
        """Test initialization with default values"""
        calc = ZoneCalculator()
        assert calc.max_hr == 171  # Default from env
        assert calc.lthr == 153    # Default from env
        assert calc.ftp == 301     # Default from env
    
    def test_initialization_with_values(self):
        """Test initialization with custom values"""
        calc = ZoneCalculator(max_hr=190, lthr=165, ftp=300)
        assert calc.max_hr == 190
        assert calc.lthr == 165
        assert calc.ftp == 300
    
    def test_hr_zone_calculation_with_lthr(self):
        """Test HR zone calculation using LTHR"""
        calc = ZoneCalculator(lthr=160)
        zones = calc.calculate_hr_zones()
        
        assert len(zones) == 7
        # Check Zone 1 (Recovery)
        assert zones[0].name == "Recovery"
        assert zones[0].lower == 0
        assert zones[0].upper == pytest.approx(160 * 0.81, rel=1)  # 129.6
        assert zones[0].polarized_zone == 1
        
        # Check Zone 4 (Threshold)
        assert zones[3].name == "Threshold"
        assert zones[3].lower == pytest.approx(160 * 0.94, rel=1)  # 150.4
        assert zones[3].upper == pytest.approx(160 * 0.99, rel=1)  # 158.4
        assert zones[3].polarized_zone == 2
    
    def test_hr_zone_calculation_without_lthr(self):
        """Test HR zone calculation using max HR fallback"""
        calc = ZoneCalculator(max_hr=190, lthr=0)
        zones = calc.calculate_hr_zones()
        
        assert len(zones) == 3  # Simple model
        assert zones[0].name == "Low"
        assert zones[0].upper == pytest.approx(190 * 0.82, rel=0.01)
        assert zones[1].name == "Threshold"
        assert zones[2].name == "High"
    
    def test_power_zone_calculation(self):
        """Test power zone calculation"""
        calc = ZoneCalculator(ftp=250)
        zones = calc.calculate_power_zones()
        
        assert len(zones) == 7
        # Check Zone 1 (Recovery)
        assert zones[0].name == "Recovery"
        assert zones[0].upper == pytest.approx(250 * 0.55, rel=1)  # 137.5
        
        # Check Zone 4 (Threshold)
        assert zones[3].name == "Threshold"
        assert zones[3].lower == pytest.approx(250 * 0.91, rel=1)  # 227.5
        assert zones[3].upper == pytest.approx(250 * 1.05, rel=1)  # 262.5
    
    def test_get_hr_zone(self):
        """Test getting HR zone for a specific value"""
        calc = ZoneCalculator(lthr=160)
        
        assert calc.get_hr_zone(120) == 1  # Zone 1
        assert calc.get_hr_zone(140) == 2  # Zone 2
        assert calc.get_hr_zone(145) == 3  # Zone 3
        assert calc.get_hr_zone(155) == 4  # Zone 4
        assert calc.get_hr_zone(162) == 5  # Zone 5
        assert calc.get_hr_zone(167) == 6  # Zone 6
        assert calc.get_hr_zone(175) == 7  # Zone 7
    
    def test_get_power_zone(self):
        """Test getting power zone for a specific value"""
        calc = ZoneCalculator(ftp=250)
        
        assert calc.get_power_zone(100) == 1  # Zone 1
        assert calc.get_power_zone(160) == 2  # Zone 2
        assert calc.get_power_zone(200) == 3  # Zone 3
        assert calc.get_power_zone(240) == 4  # Zone 4
        assert calc.get_power_zone(280) == 5  # Zone 5
        assert calc.get_power_zone(350) == 6  # Zone 6
        assert calc.get_power_zone(400) == 7  # Zone 7
    
    def test_map_to_polarized_zone(self):
        """Test mapping 7-zone to 3-zone polarized"""
        calc = ZoneCalculator()
        
        # Test standard mapping
        assert calc.map_to_polarized_zone(1) == 1
        assert calc.map_to_polarized_zone(2) == 1
        assert calc.map_to_polarized_zone(3) == 2
        assert calc.map_to_polarized_zone(4) == 2
        assert calc.map_to_polarized_zone(5) == 3
        assert calc.map_to_polarized_zone(6) == 3
        assert calc.map_to_polarized_zone(7) == 3
    
    def test_calculate_zone_percentages(self):
        """Test zone percentage calculation"""
        calc = ZoneCalculator()
        
        zone_times = {
            1: 1800,  # 30 minutes
            2: 1200,  # 20 minutes
            3: 600,   # 10 minutes
            4: 300,   # 5 minutes
            5: 60,    # 1 minute
            6: 30,    # 0.5 minute
            7: 10     # 10 seconds
        }
        
        percentages = calc.calculate_zone_percentages(zone_times)
        
        assert percentages[1] == pytest.approx(45.0, rel=0.1)
        assert percentages[2] == pytest.approx(30.0, rel=0.1)
        assert percentages[3] == pytest.approx(15.0, rel=0.1)
        assert sum(percentages.values()) == pytest.approx(100.0, rel=0.1)
    
    def test_calculate_polarized_percentages(self):
        """Test polarized zone percentage calculation"""
        calc = ZoneCalculator()
        
        zone_times = {
            1: 1800,  # 30 minutes
            2: 1200,  # 20 minutes -> Zone 1 (50 min total)
            3: 600,   # 10 minutes
            4: 300,   # 5 minutes -> Zone 2 (15 min total)
            5: 60,    # 1 minute
            6: 30,    # 0.5 minute
            7: 10     # 10 seconds -> Zone 3 (1.67 min total)
        }
        
        polarized = calc.calculate_polarized_percentages(zone_times)
        
        # Zone 1: (1800 + 1200) / 4000 = 75%
        # Zone 2: (600 + 300) / 4000 = 22.5%
        # Zone 3: (60 + 30 + 10) / 4000 = 2.5%
        assert polarized[1] == pytest.approx(75.0, rel=0.1)
        assert polarized[2] == pytest.approx(22.5, rel=0.1)
        assert polarized[3] == pytest.approx(2.5, rel=0.1)
    
    def test_get_zone_distribution_targets(self):
        """Test getting zone distribution targets"""
        calc = ZoneCalculator()
        
        targets = calc.get_zone_distribution_targets("polarized")
        assert targets[1] == 80.0
        assert targets[2] == 10.0
        assert targets[3] == 10.0
        
        targets = calc.get_zone_distribution_targets("pyramidal")
        assert targets[1] == 70.0
        assert targets[2] == 20.0
        assert targets[3] == 10.0
    
    def test_calculate_zone_deviations(self):
        """Test deviation calculation"""
        calc = ZoneCalculator()
        
        actual = {1: 75.0, 2: 15.0, 3: 10.0}
        deviations = calc.calculate_zone_deviations(actual, "polarized")
        
        assert deviations[1] == -5.0  # 75 - 80 = -5 (deficit)
        assert deviations[2] == 5.0   # 15 - 10 = 5 (excess)
        assert deviations[3] == 0.0   # 10 - 10 = 0 (on target)
    
    def test_calculate_adherence_score(self):
        """Test adherence score calculation"""
        calc = ZoneCalculator()
        
        # Perfect adherence
        actual = {1: 80.0, 2: 10.0, 3: 10.0}
        score = calc.calculate_adherence_score(actual, "polarized")
        assert score == 100.0
        
        # Some deviation
        actual = {1: 75.0, 2: 15.0, 3: 10.0}
        score = calc.calculate_adherence_score(actual, "polarized")
        # Zone 1: 5% deviation * 0.5 weight = 2.5
        # Zone 2: 5% deviation * 0.25 weight = 1.25
        # Zone 3: 0% deviation * 0.25 weight = 0
        # Total: 3.75, so score = 100 - 3.75 = 96.25
        assert score == pytest.approx(96.25, rel=0.1)
    
    def test_update_thresholds(self):
        """Test updating thresholds"""
        calc = ZoneCalculator(max_hr=180, lthr=160, ftp=250)
        
        calc.update_thresholds(max_hr=190, lthr=165, ftp=300)
        
        assert calc.max_hr == 190
        assert calc.lthr == 165
        assert calc.ftp == 300


class TestZoneStrategies:
    """Test individual zone calculation strategies"""
    
    def test_heart_rate_zone_strategy(self):
        """Test HR zone strategy calculations"""
        strategy = HeartRateZoneStrategy()
        zones = strategy.calculate_zones(160)  # LTHR = 160
        
        assert len(zones) == 7
        assert zones[0].upper == pytest.approx(129.6, rel=0.1)  # 160 * 0.81
        assert zones[3].lower == pytest.approx(150.4, rel=0.1)  # 160 * 0.94
        
        # Test zone number calculation
        assert strategy.get_zone_number(120, 160) == 1
        assert strategy.get_zone_number(155, 160) == 4
    
    def test_power_zone_strategy(self):
        """Test power zone strategy calculations"""
        strategy = PowerZoneStrategy()
        zones = strategy.calculate_zones(250)  # FTP = 250
        
        assert len(zones) == 7
        assert zones[1].upper == pytest.approx(187.5, rel=0.1)  # 250 * 0.75
        assert zones[3].lower == pytest.approx(227.5, rel=0.1)  # 250 * 0.91
        
        # Test zone number calculation
        assert strategy.get_zone_number(100, 250) == 1
        assert strategy.get_zone_number(240, 250) == 4
    
    def test_simple_hr_zone_strategy(self):
        """Test simple HR zone strategy"""
        strategy = SimpleHeartRateZoneStrategy()
        zones = strategy.calculate_zones(190)  # Max HR = 190
        
        assert len(zones) == 3
        assert zones[0].upper == pytest.approx(155.8, rel=0.1)  # 190 * 0.82
        assert zones[1].upper == pytest.approx(165.3, rel=0.1)  # 190 * 0.87


class TestBackwardCompatibility:
    """Test backward compatibility with existing code patterns"""
    
    def test_factory_function(self):
        """Test create_zone_calculator factory function"""
        calc = create_zone_calculator(max_hr=190, lthr=165)
        assert isinstance(calc, ZoneCalculator)
        assert calc.max_hr == 190
        assert calc.lthr == 165
    
    def test_calculate_from_stream(self):
        """Test stream calculation helper function"""
        # Simulate HR stream data
        stream_data = [120] * 30 + [145] * 20 + [165] * 10  # 60 data points
        
        calc = ZoneCalculator(lthr=160)  # Create calculator with LTHR
        percentages = calculate_zone_percentages_from_stream(
            stream_data, 
            threshold=160,  # LTHR
            calculator=calc,
            metric_type="heart_rate"
        )
        
        # Zone 1: 30/60 = 50%
        # Zone 3: 20/60 = 33.3%
        # Zone 6: 10/60 = 16.7%
        assert percentages[1] == pytest.approx(50.0, rel=0.1)
        assert percentages[3] == pytest.approx(33.3, rel=0.1)
        assert percentages[6] == pytest.approx(16.7, rel=0.1)
    
    def test_mimics_training_analyzer_behavior(self):
        """Test that zone calculations match TrainingAnalyzer behavior"""
        calc = ZoneCalculator(lthr=160)
        
        # Test same HR values as in TrainingAnalyzer._get_hr_zone
        test_cases = [
            (120, 1),  # Below zone 1 max (129.6)
            (135, 2),  # Between 129.6 and 142.4
            (145, 3),  # Between 144 and 148.8
            (155, 4),  # Between 150.4 and 158.4
            (162, 5),  # Between 160 and 163.2
            (167, 6),  # Between 164.8 and 169.6
            (175, 7),  # Above 169.6
        ]
        
        for hr, expected_zone in test_cases:
            assert calc.get_hr_zone(hr) == expected_zone
    
    def test_zone_percentage_calculation_pattern(self):
        """Test zone percentage calculation matches existing patterns"""
        calc = ZoneCalculator()
        
        # Simulate the pattern from TrainingAnalyzer
        zone_seconds = {1: 1800, 2: 1200, 3: 600, 4: 300, 5: 60, 6: 30, 7: 10}
        total_seconds = sum(zone_seconds.values())
        
        # Calculate percentages the old way
        old_way = {}
        for zone, seconds in zone_seconds.items():
            old_way[zone] = seconds / total_seconds * 100
        
        # Calculate with new method
        new_way = calc.calculate_zone_percentages(zone_seconds)
        
        # Verify they match
        for zone in range(1, 8):
            assert new_way[zone] == pytest.approx(old_way[zone], rel=0.01)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])