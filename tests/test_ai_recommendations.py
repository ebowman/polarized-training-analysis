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
        
        # Verify structure of first recommendation pathway
        pathway = recommendations[0]
        assert pathway.pathway_name is not None
        assert pathway.today.workout_type == "easy_aerobic"
        assert 1 in pathway.today.intensity_zones
        assert pathway.today.duration_minutes == 60
        assert pathway.priority == "high"
        
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
        # Check it's a fallback recommendation pathway
        assert recommendations[0].pathway_name == "Fallback Pathway"
        assert recommendations[0].today.workout_type in ["easy_aerobic", "recovery", "Fallback Workout"]
    
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
    
    def test_ai_pathway_recommendations(self, ai_engine):
        """Test AI pathway recommendation generation"""
        training_data = {
            'activities': [
                {
                    'name': 'Morning Run',
                    'date': datetime.now().isoformat(),
                    'duration_minutes': 45,
                    'zone1_percent': 80,
                    'zone2_percent': 15,
                    'zone3_percent': 5
                }
            ]
        }
        
        pathway_context = {
            'deficit': 120,
            'currentWeeklyMinutes': 240,
            'targetWeeklyMinutes': 360,
            'todayMinutes': 0,
            'alreadyWorkedOutToday': False,
            'dayOfWeek': 'Monday'
        }
        
        # Mock the provider to return pathway recommendations
        ai_engine.provider.generate_completion.return_value = json.dumps({
            'aggressive': {
                'workout_type': 'Interval Training',
                'duration_minutes': 60,
                'description': 'High-intensity intervals',
                'structure': '5 min warm-up, 8x2 min intervals, 5 min cool-down',
                'reasoning': 'Quick volume recovery',
                'equipment': 'Treadmill',
                'intensity_zones': [3],
                'priority': 'high'
            },
            'steady': {
                'workout_type': 'Tempo Run',
                'duration_minutes': 45,
                'description': 'Moderate tempo workout',
                'structure': '10 min warm-up, 25 min tempo, 10 min cool-down',
                'reasoning': 'Balanced approach',
                'equipment': 'Treadmill',
                'intensity_zones': [2],
                'priority': 'medium'
            },
            'conservative': {
                'workout_type': 'Easy Run',
                'duration_minutes': 30,
                'description': 'Easy recovery run',
                'structure': '30 min at easy pace',
                'reasoning': 'Gentle volume building',
                'equipment': 'Treadmill',
                'intensity_zones': [1],
                'priority': 'low'
            }
        })
        
        pathways = ai_engine.generate_pathway_recommendations(training_data, pathway_context)
        
        assert isinstance(pathways, dict)
        assert 'aggressive' in pathways
        assert 'steady' in pathways
        assert 'conservative' in pathways
        
        # Verify aggressive pathway
        aggressive = pathways['aggressive']
        assert aggressive.workout_type == 'Interval Training'
        assert aggressive.duration_minutes == 60
        assert 3 in aggressive.intensity_zones
        assert aggressive.priority == 'high'
    
    def test_training_data_analyzer(self):
        """Test TrainingDataAnalyzer component"""
        from ai_recommendations import TrainingDataAnalyzer
        
        analyzer = TrainingDataAnalyzer()
        
        # Test with realistic training data
        training_data = {
            'activities': [
                {
                    'name': 'Morning Ride',
                    'date': (datetime.now() - timedelta(days=1)).isoformat(),
                    'duration_minutes': 90,
                    'zone1_percent': 70,
                    'zone2_percent': 20,
                    'zone3_percent': 10
                },
                {
                    'name': 'Recovery Run',
                    'date': (datetime.now() - timedelta(days=2)).isoformat(),
                    'duration_minutes': 45,
                    'zone1_percent': 95,
                    'zone2_percent': 5,
                    'zone3_percent': 0
                }
            ]
        }
        
        analysis = analyzer.analyze_training_data(training_data)
        
        assert analysis.total_minutes == 135
        assert analysis.total_activities == 2
        assert analysis.weekly_hours == 2.25
        assert analysis.training_approach == 'low-volume'
        assert analysis.zone1_percent > 70
        assert analysis.adherence_score > 0
    
    def test_recovery_metrics_calculation(self):
        """Test recovery metrics calculation"""
        from ai_recommendations import TrainingDataAnalyzer
        
        analyzer = TrainingDataAnalyzer()
        
        # Create activities for last week
        activities = []
        for i in range(7):
            activities.append({
                'name': f'Workout {i}',
                'date': (datetime.now() - timedelta(days=i)).isoformat(),
                'duration_minutes': 60,
                'zone1_percent': 70,
                'zone2_percent': 20,
                'zone3_percent': 10
            })
        
        metrics = analyzer.calculate_recovery_metrics(activities)
        
        assert isinstance(metrics, dict)
        assert 'consecutive_training_days' in metrics
        assert 'zone3_last_3_days' in metrics
        assert 'total_minutes_last_3_days' in metrics
        assert 'trained_today' in metrics
        assert 'weekly_volume_change' in metrics
        
        # Should detect consecutive training days
        assert metrics['consecutive_training_days'] > 0
        assert metrics['total_minutes_last_3_days'] > 0
    
    def test_prompt_builder(self):
        """Test PromptBuilder component"""
        from ai_recommendations import PromptBuilder
        
        builder = PromptBuilder()
        
        training_data = {
            'activities': [
                {
                    'name': 'Test Workout',
                    'date': datetime.now().isoformat(),
                    'duration_minutes': 60,
                    'zone1_percent': 80,
                    'zone2_percent': 15,
                    'zone3_percent': 5
                }
            ],
            'config': {
                'lthr': 165,
                'ftp': 250,
                'max_hr': 180
            }
        }
        
        prompt = builder.build_prompt(training_data, num_recommendations=3)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 1000  # Should be comprehensive
        assert 'Zone 1' in prompt
        assert 'Zone 2' in prompt
        assert 'Zone 3' in prompt
        assert 'polarized' in prompt.lower()
        assert 'recommendations' in prompt.lower()
    
    def test_equipment_detection(self):
        """Test equipment detection from preferences"""
        from ai_recommendations import PromptBuilder
        
        builder = PromptBuilder()
        
        # Mock preferences file with equipment mentions
        preferences_content = """
        # My Training Preferences
        
        ## Equipment Available
        - Road bike (Giant TCR)
        - Gym access at Soho House
        - Swimming pool access
        
        ## Goals
        - Build aerobic base
        - Improve FTP
        """
        
        with patch('builtins.open', mock_open(read_data=preferences_content)):
            equipment = builder._get_available_equipment()
            
            assert 'Road Bike' in equipment
            assert 'Gym Equipment' in equipment
            assert 'Swimming Pool' in equipment
    
    def test_heart_rate_zone_processing(self):
        """Test heart rate zone processing with LTHR"""
        from ai_recommendations import PromptBuilder
        
        builder = PromptBuilder()
        
        # Test with LTHR set
        with patch.dict(os.environ, {'AVERAGE_FTP_HR': '165'}):
            content = "Your max HR is 171 bpm and zones are 120-140 bpm for aerobic."
            processed = builder._process_hr_ranges(content)
            
            # Should replace with LTHR-based ranges
            assert '133-146 bpm' in processed  # 0.81-0.89 * 165
            assert '165 bpm' in processed  # LTHR reference
    
    def test_ai_recommendation_history(self, ai_engine):
        """Test AI recommendation history saving and loading"""
        # Create mock recommendations
        from ai_recommendations import AIWorkoutPathway, AIWorkoutRecommendation
        
        workout = AIWorkoutRecommendation(
            workout_type='Test Workout',
            duration_minutes=60,
            description='Test description',
            structure='Test structure',
            reasoning='Test reasoning',
            equipment='Test equipment',
            intensity_zones=[1],
            priority='medium',
            generated_at=datetime.now().isoformat()
        )
        
        pathway = AIWorkoutPathway(
            pathway_name='Test Pathway',
            today=workout,
            tomorrow=workout,
            overall_reasoning='Test overall reasoning',
            priority='medium',
            generated_at=datetime.now().isoformat()
        )
        
        recommendations = [pathway]
        
        # Test saving
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.exists', return_value=False):
                ai_engine.save_recommendation_history(recommendations)
                mock_file.assert_called_once()
        
        # Test loading
        history_data = [{
            'timestamp': datetime.now().isoformat(),
            'recommendations': [{
                'pathway_name': 'Test Pathway',
                'today': {
                    'workout_type': 'Test Workout',
                    'duration_minutes': 60
                },
                'tomorrow': {
                    'workout_type': 'Test Workout',
                    'duration_minutes': 60
                }
            }]
        }]
        
        with patch('builtins.open', mock_open(read_data=json.dumps(history_data))):
            history = ai_engine.load_recommendation_history()
            assert len(history) == 1
            assert history[0]['recommendations'][0]['pathway_name'] == 'Test Pathway'
    
    def test_ai_provider_integration(self):
        """Test AI provider integration"""
        from ai_providers import AIProviderFactory, OpenAIProvider, ClaudeProvider
        
        # Test provider factory
        provider = AIProviderFactory.create_provider()
        assert provider is not None
        
        # Test with mock provider
        mock_provider = MagicMock()
        mock_provider.get_provider_name.return_value = "TestProvider"
        mock_provider.generate_completion.return_value = json.dumps([
            {
                'pathway_name': 'Test Pathway',
                'today': {
                    'workout_type': 'Test Workout',
                    'duration_minutes': 60,
                    'description': 'Test description',
                    'structure': 'Test structure',
                    'reasoning': 'Test reasoning',
                    'equipment': 'Test equipment',
                    'intensity_zones': [1]
                },
                'tomorrow': {
                    'workout_type': 'Test Workout 2',
                    'duration_minutes': 45,
                    'description': 'Test description 2',
                    'structure': 'Test structure 2',
                    'reasoning': 'Test reasoning 2',
                    'equipment': 'Test equipment 2',
                    'intensity_zones': [2]
                },
                'overall_reasoning': 'Test overall reasoning',
                'priority': 'medium'
            }
        ])
        
        engine = AIRecommendationEngine(provider=mock_provider)
        recommendations = engine.generate_ai_recommendations({'activities': []})
        
        assert len(recommendations) == 1
        assert recommendations[0].pathway_name == 'Test Pathway'
        assert recommendations[0].today.workout_type == 'Test Workout'
        assert recommendations[0].tomorrow.workout_type == 'Test Workout 2'
    
    def test_sport_config_integration(self):
        """Test integration with sport configuration system"""
        # Mock sport config service
        mock_service = MagicMock()
        mock_service.get_zone_distribution_target.return_value = {1: 80, 2: 10, 3: 10}
        
        with patch('ai_recommendations.SportConfigService', return_value=mock_service):
            from ai_recommendations import TrainingDataAnalyzer
            
            analyzer = TrainingDataAnalyzer()
            
            # Test adherence calculation with sport config
            score = analyzer.calculate_adherence_score(75, 15, 10, 'polarized')
            assert score > 0
            
            # Verify sport config was used
            mock_service.get_zone_distribution_target.assert_called_once()
    
    def test_multi_provider_fallback(self):
        """Test fallback between multiple AI providers"""
        engine = AIRecommendationEngine()
        
        # Test with provider that fails
        failing_provider = MagicMock()
        failing_provider.get_provider_name.return_value = "FailingProvider"
        failing_provider.generate_completion.side_effect = Exception("API unavailable")
        
        engine.provider = failing_provider
        
        # Should return fallback recommendations
        recommendations = engine.generate_ai_recommendations({'activities': []})
        assert len(recommendations) > 0
        assert recommendations[0].pathway_name == 'Fallback Pathway'
    
    def test_complex_training_scenarios(self):
        """Test complex training scenarios"""
        from ai_recommendations import TrainingDataAnalyzer
        
        analyzer = TrainingDataAnalyzer()
        
        # Scenario 1: Overtraining - too much zone 3
        overtraining_data = {
            'activities': [
                {
                    'name': 'Hard Intervals',
                    'date': (datetime.now() - timedelta(days=i)).isoformat(),
                    'duration_minutes': 60,
                    'zone1_percent': 40,
                    'zone2_percent': 30,
                    'zone3_percent': 30
                } for i in range(7)
            ]
        }
        
        analysis = analyzer.analyze_training_data(overtraining_data)
        assert analysis.zone3_percent > 20  # Should detect high zone 3
        
        # Scenario 2: Insufficient intensity
        low_intensity_data = {
            'activities': [
                {
                    'name': 'Easy Ride',
                    'date': (datetime.now() - timedelta(days=i)).isoformat(),
                    'duration_minutes': 90,
                    'zone1_percent': 95,
                    'zone2_percent': 5,
                    'zone3_percent': 0
                } for i in range(7)
            ]
        }
        
        analysis = analyzer.analyze_training_data(low_intensity_data)
        assert analysis.zone3_percent < 5  # Should detect low zone 3
        assert analysis.training_approach == 'polarized'  # High volume
    
    def test_error_recovery_and_retries(self, ai_engine):
        """Test error recovery and retry mechanisms"""
        # Test retry logic
        ai_engine.provider.generate_completion.side_effect = [
            Exception("Temporary error"),
            Exception("Another error"),
            json.dumps([{
                'pathway_name': 'Recovery Pathway',
                'today': {
                    'workout_type': 'Rest Day',
                    'duration_minutes': 0,
                    'description': 'Complete rest',
                    'structure': 'No training',
                    'reasoning': 'Recovery needed',
                    'equipment': 'None',
                    'intensity_zones': []
                },
                'tomorrow': {
                    'workout_type': 'Easy Recovery',
                    'duration_minutes': 30,
                    'description': 'Light activity',
                    'structure': '30 min easy',
                    'reasoning': 'Gentle return',
                    'equipment': 'Bodyweight',
                    'intensity_zones': [1]
                },
                'overall_reasoning': 'Recovery focus',
                'priority': 'high'
            }])
        ]
        
        recommendations = ai_engine.generate_ai_recommendations({'activities': []})
        
        # Should succeed after retries
        assert len(recommendations) == 1
        assert recommendations[0].pathway_name == 'Recovery Pathway'
        
        # Verify all attempts were made
        assert ai_engine.provider.generate_completion.call_count == 3