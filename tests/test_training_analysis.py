"""
Unit tests for training_analysis.py
Tests the core training analysis logic including zone calculations and adherence scoring
"""

import pytest
from datetime import datetime, timedelta
from training_analysis import TrainingZones, PowerZones, TrainingAnalyzer, ActivityAnalysis


class TestTrainingZones:
    """Test the TrainingZones class for heart rate zone calculations"""
    
    def test_from_lthr_calculations(self):
        """Test zone calculations from LTHR (Lactate Threshold Heart Rate)"""
        zones = TrainingZones.from_lthr(170)
        
        # Verify zone calculations match expected percentages
        assert zones.zone1_max == 137  # 81% of 170
        assert zones.zone2_max == 151  # 89% of 170
        assert zones.zone3_max == 158  # 93% of 170
        assert zones.zone4_max == 168  # 99% of 170
        assert zones.zone5a_max == 173  # 102% of 170
        assert zones.zone5b_max == 180  # 106% of 170
        assert zones.zone5c_min == 180  # >106% of 170
        assert zones.lthr == 170
    
    def test_from_max_hr(self):
        """Test zone calculations from max heart rate"""
        zones = TrainingZones.from_max_hr(190)
        
        # Verify zones are created (even if simplified)
        assert zones.zone1_max == 155  # ~82% of 190
        assert zones.lthr == 171  # ~90% of 190
    
    def test_edge_cases(self):
        """Test edge cases for zone calculations"""
        # Test with very low LTHR
        zones_low = TrainingZones.from_lthr(100)
        assert zones_low.zone1_max == 81
        
        # Test with very high LTHR
        zones_high = TrainingZones.from_lthr(200)
        assert zones_high.zone1_max == 162


class TestPowerZones:
    """Test the PowerZones class for cycling power calculations"""
    
    def test_from_ftp_calculations(self):
        """Test cycling power zones from FTP (Functional Threshold Power)"""
        zones = PowerZones.from_ftp(250)
        
        # Verify power zone calculations
        assert zones.zone1_max == 137  # 55% of 250
        assert zones.zone2_max == 187  # 75% of 250
        assert zones.zone3_max == 225  # 90% of 250
        assert zones.zone4_max == 262  # 105% of 250
        assert zones.zone5_max == 300  # 120% of 250
        assert zones.zone6_max == 375  # 150% of 250
        assert zones.zone7_min == 375  # >150% of 250
        assert zones.ftp == 250


class TestActivityAnalysis:
    """Test the ActivityAnalysis dataclass"""
    
    def test_activity_creation(self):
        """Test creating an activity analysis with all fields"""
        activity = ActivityAnalysis(
            activity_id=12345,
            name="Morning Run",
            date=datetime.now().isoformat(),
            sport_type="Run",
            duration_minutes=60,
            zone1_minutes=40,
            zone2_minutes=15,
            zone3_minutes=5,
            zone1_percent=66.7,
            zone2_percent=25.0,
            zone3_percent=8.3,
            average_hr=145,
            average_power=None
        )
        
        assert activity.activity_id == 12345
        assert activity.duration_minutes == 60
        assert activity.average_hr == 145
        assert activity.average_power is None


class TestTrainingAnalyzer:
    """Test the main TrainingAnalyzer class"""
    
    @pytest.fixture
    def analyzer(self):
        """Create a TrainingAnalyzer instance"""
        return TrainingAnalyzer()
    
    @pytest.fixture
    def sample_strava_activities(self):
        """Create sample Strava activity data"""
        base_date = datetime.now()
        return [
            {
                'id': 1,
                'name': 'Easy Run',
                'type': 'Run',
                'start_date': (base_date - timedelta(days=1)).isoformat() + 'Z',
                'elapsed_time': 3600,  # 1 hour
                'distance': 10000,
                'average_heartrate': 130,
                'max_heartrate': 145,
                'has_heartrate': True
            },
            {
                'id': 2,
                'name': 'Threshold Run',
                'type': 'Run',
                'start_date': (base_date - timedelta(days=2)).isoformat() + 'Z',
                'elapsed_time': 2400,  # 40 minutes
                'distance': 8000,
                'average_heartrate': 165,
                'max_heartrate': 175,
                'has_heartrate': True
            }
        ]
    
    def test_analyze_activities(self, analyzer, sample_strava_activities):
        """Test analyzing multiple activities"""
        results, ancillary_work = analyzer.analyze_activities(sample_strava_activities)
        
        # Should return tuple of (list of ActivityAnalysis objects, ancillary work dict)
        assert isinstance(results, list)
        assert isinstance(ancillary_work, dict)
        assert len(results) > 0
        
        # Check first activity
        if results:
            first = results[0]
            assert isinstance(first, ActivityAnalysis)
            assert first.name == 'Easy Run'
            assert first.duration_minutes == 60
    
    def test_analyze_activity_without_hr_or_power(self, analyzer):
        """Test handling activities without heart rate or power data"""
        activity = {
            'id': 3,
            'name': 'Yoga Session',
            'type': 'Yoga',
            'start_date': datetime.now().isoformat() + 'Z',
            'elapsed_time': 3600,
            'has_heartrate': False
        }
        
        results, ancillary_work = analyzer.analyze_activities([activity])
        
        # Should return empty list for activities without HR/power
        assert results == []
        assert isinstance(ancillary_work, dict)
    
    def test_calculate_training_distribution(self, analyzer):
        """Test training distribution calculation"""
        # Create sample analyzed activities
        activities = [
            ActivityAnalysis(
                activity_id=1,
                name="Easy Run",
                date=datetime.now().isoformat(),
                sport_type="Run",
                duration_minutes=60,
                zone1_minutes=50,
                zone2_minutes=8,
                zone3_minutes=2,
                zone1_percent=83.3,
                zone2_percent=13.3,
                zone3_percent=3.3,
                average_hr=130
            ),
            ActivityAnalysis(
                activity_id=2,
                name="Hard Run",
                date=datetime.now().isoformat(),
                sport_type="Run",
                duration_minutes=40,
                zone1_minutes=10,
                zone2_minutes=20,
                zone3_minutes=10,
                zone1_percent=25.0,
                zone2_percent=50.0,
                zone3_percent=25.0,
                average_hr=165
            )
        ]
        
        distribution = analyzer.calculate_training_distribution(activities)
        
        # Check that distribution is calculated
        assert hasattr(distribution, 'zone1_percent')
        assert hasattr(distribution, 'zone2_percent')
        assert hasattr(distribution, 'zone3_percent')
        assert hasattr(distribution, 'total_minutes')
        
        # Total should be 100 minutes (60 + 40)
        assert distribution.total_minutes == 100
        
        # Percentages should add up to ~100
        total_percent = distribution.zone1_percent + distribution.zone2_percent + distribution.zone3_percent
        assert 99 <= total_percent <= 101  # Allow for rounding
    
    def test_empty_activities_handling(self, analyzer):
        """Test handling of empty activity list"""
        results, ancillary_work = analyzer.analyze_activities([])
        assert results == []
        assert isinstance(ancillary_work, dict)
        
        # Test distribution with no activities
        distribution = analyzer.calculate_training_distribution([])
        assert distribution.total_minutes == 0
        assert distribution.zone1_percent == 0
        assert distribution.zone2_percent == 0
        assert distribution.zone3_percent == 0