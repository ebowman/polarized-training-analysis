"""
Unit tests for ai_recommendations.py
Tests AI recommendation generation with mocked OpenAI API
"""

import pytest
from unittest.mock import patch, MagicMock, Mock, mock_open
from datetime import datetime, timedelta
import json
import os
from ai_recommendations import AIRecommendationEngine


class TestAIRecommendations:
    """Test AI recommendation functionality"""
    
    @pytest.fixture
    def ai_engine(self):
        """Create an AI recommendation engine instance"""
        # Mock the provider
        mock_provider = MagicMock()
        mock_provider.get_provider_name.return_value = "MockProvider"
        mock_provider.generate_completion.return_value = json.dumps([
            {
                "workout_type": "easy_aerobic",
                "primary_zone": 1,
                "duration_minutes": 60,
                "description": "Easy recovery run",
                "structure": "60 minutes at easy pace",
                "reasoning": "Recovery from recent hard efforts",
                "equipment": "Running shoes",
                "intensity_zones": [1],
                "priority": "high"
            }
        ])
        
        # Create engine with mocked provider
        engine = AIRecommendationEngine(provider=mock_provider)
        return engine
    
    @pytest.fixture
    def sample_training_analysis(self):
        """Create sample training analysis data"""
        return {
            'current_distribution': {'zone1': 70, 'zone2': 20, 'zone3': 10},
            'target_distribution': {'zone1': 80, 'zone2': 10, 'zone3': 10},
            'adherence_score': 75,
            'total_time': 8.5,
            'workouts': [
                {
                    'name': 'Easy Run',
                    'date': (datetime.now() - timedelta(days=1)).isoformat(),
                    'duration': 1.0,
                    'sport': 'Run',
                    'zones': {'zone1': 80, 'zone2': 20, 'zone3': 0}
                },
                {
                    'name': 'Threshold Intervals',
                    'date': (datetime.now() - timedelta(days=2)).isoformat(),
                    'duration': 1.5,
                    'sport': 'Ride',
                    'zones': {'zone1': 40, 'zone2': 40, 'zone3': 20}
                }
            ]
        }
    
    def test_generate_recommendations_success(self, ai_engine, sample_training_analysis):
        """Test successful AI recommendation generation"""
        # Generate recommendations using mocked provider
        recommendations = ai_engine.generate_ai_recommendations(sample_training_analysis)
        
        # Verify recommendations were generated
        assert recommendations is not None
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Verify structure of first recommendation
        rec = recommendations[0]
        assert rec.workout_type == "easy_aerobic"
        assert 1 in rec.intensity_zones
        assert rec.duration_minutes == 60
        assert rec.priority == "high"
        
        # Verify provider was called
        ai_engine.provider.generate_completion.assert_called()
    
    def test_generate_recommendations_api_error(self, ai_engine, sample_training_analysis):
        """Test handling of AI provider API errors"""
        # Make the provider raise an exception
        ai_engine.provider.generate_completion.side_effect = Exception("API Error: Rate limit exceeded")
        
        # The method should handle the error gracefully and return fallback recommendations
        recommendations = ai_engine.generate_ai_recommendations(sample_training_analysis)
        
        # Should return a list with at least one fallback recommendation
        assert recommendations is not None
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        # Check it's a fallback recommendation
        assert recommendations[0].workout_type in ["easy_aerobic", "recovery", "Fallback Workout"]
    
    def test_format_analysis_for_ai(self, ai_engine, sample_training_analysis):
        """Test formatting training data for AI prompt"""
        formatted = ai_engine.format_analysis_for_ai(sample_training_analysis)
        
        # Verify key information is included
        assert '70%' in formatted  # Zone 1 percentage
        assert '20%' in formatted  # Zone 2 percentage
        assert '10%' in formatted  # Zone 3 percentage
        assert '8.5 hours' in formatted  # Total time
        assert 'Easy Run' in formatted  # Workout name
    
    @patch('builtins.open', new_callable=mock_open, read_data='# Workout Preferences\n\nEquipment: Peloton')
    @patch('os.path.exists', return_value=True)
    def test_load_preferences(self, mock_exists, mock_file, ai_engine):
        """Test loading workout preferences"""
        prefs = ai_engine.load_preferences()
        
        assert prefs is not None
        assert 'Equipment: Peloton' in prefs
    
    def test_parse_workout_recommendation(self, ai_engine):
        """Test parsing AI response into structured recommendation"""
        ai_response = """## Monday: Easy Recovery Run
Duration: 45 minutes
Intensity: Zone 1 (65-75% LTHR)
Structure: 
- 10 min warm-up walk
- 30 min easy run
- 5 min cool-down walk

Purpose: Active recovery to promote blood flow"""
        
        recommendation = ai_engine.parse_recommendation(ai_response)
        
        assert recommendation is not None
        # The actual parsing logic would depend on implementation
    
    def test_validate_recommendation(self, ai_engine):
        """Test validation of AI recommendations"""
        valid_recommendation = {
            'workout_type': 'Easy Run',
            'duration_minutes': 45,
            'intensity_zones': [1],
            'description': 'Easy recovery run'
        }
        
        invalid_recommendation = {
            'workout_type': 'Easy Run',
            'duration_minutes': 500,  # Too long
            'intensity_zones': [7],  # Invalid zone
        }
        
        # Validation logic would depend on implementation
        assert ai_engine.is_valid_recommendation(valid_recommendation) == True
        assert ai_engine.is_valid_recommendation(invalid_recommendation) == False
    
    def test_caching_recommendations(self, ai_engine):
        """Test caching of AI recommendations"""
        session_id = 'test_session_123'
        recommendations = 'Test workout plan'
        
        # Save recommendations
        ai_engine.save_recommendations(session_id, recommendations)
        
        # Load recommendations
        loaded = ai_engine.load_recommendations(session_id)
        
        assert loaded == recommendations
    
    def test_training_approach_detection(self, ai_engine):
        """Test detection of training approach based on volume"""
        # Low volume
        low_volume_analysis = {'total_time': 3.5}
        approach = ai_engine.determine_training_approach(low_volume_analysis)
        assert approach == 'low-volume'
        
        # Pyramidal volume
        pyramidal_analysis = {'total_time': 5.5}
        approach = ai_engine.determine_training_approach(pyramidal_analysis)
        assert approach == 'pyramidal'
        
        # Polarized volume
        polarized_analysis = {'total_time': 8.0}
        approach = ai_engine.determine_training_approach(polarized_analysis)
        assert approach == 'polarized'