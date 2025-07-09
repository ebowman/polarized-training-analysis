"""
Shared pytest fixtures and configuration
Used across all test modules
"""

import pytest
import json
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch


@pytest.fixture
def sample_strava_activities():
    """Sample Strava API activity response data"""
    base_date = datetime.now()
    return [
        {
            "id": 12345678,
            "name": "Morning Run",
            "type": "Run",
            "sport_type": "Run",
            "start_date": (base_date - timedelta(days=1)).isoformat() + "Z",
            "start_date_local": (base_date - timedelta(days=1)).isoformat() + "Z",
            "elapsed_time": 3600,
            "moving_time": 3500,
            "distance": 10000.0,
            "average_speed": 2.8,
            "max_speed": 4.2,
            "average_heartrate": 145.5,
            "max_heartrate": 175,
            "has_heartrate": True,
            "average_watts": None,
            "weighted_average_watts": None,
            "kilojoules": None,
            "device_watts": False,
            "has_kudoed": False,
            "suffer_score": 65
        },
        {
            "id": 12345679,
            "name": "Evening Ride",
            "type": "Ride",
            "sport_type": "Ride",
            "start_date": (base_date - timedelta(days=2)).isoformat() + "Z",
            "start_date_local": (base_date - timedelta(days=2)).isoformat() + "Z",
            "elapsed_time": 5400,
            "moving_time": 5200,
            "distance": 30000.0,
            "average_speed": 5.8,
            "max_speed": 12.5,
            "average_heartrate": 135.2,
            "max_heartrate": 165,
            "has_heartrate": True,
            "average_watts": 185.5,
            "weighted_average_watts": 190,
            "kilojoules": 950.5,
            "device_watts": True,
            "has_kudoed": True,
            "suffer_score": 120
        },
        {
            "id": 12345680,
            "name": "Recovery Row",
            "type": "Rowing",
            "sport_type": "Rowing",
            "start_date": (base_date - timedelta(days=3)).isoformat() + "Z",
            "start_date_local": (base_date - timedelta(days=3)).isoformat() + "Z",
            "elapsed_time": 2400,
            "moving_time": 2400,
            "distance": 6000.0,
            "average_speed": 2.5,
            "max_speed": 3.0,
            "average_heartrate": 125.0,
            "max_heartrate": 140,
            "has_heartrate": True,
            "average_watts": None,
            "weighted_average_watts": None,
            "kilojoules": None,
            "device_watts": False,
            "has_kudoed": False,
            "suffer_score": 30
        }
    ]


@pytest.fixture
def sample_activity_details():
    """Sample detailed activity data with zones"""
    return {
        "id": 12345678,
        "name": "Morning Run",
        "type": "Run",
        "elapsed_time": 3600,
        "distance": 10000.0,
        "average_heartrate": 145.5,
        "max_heartrate": 175,
        "zones": [
            {"type": "heartrate", "distribution_buckets": [
                {"min": 0, "max": 120, "time": 600},      # Zone 1
                {"min": 120, "max": 140, "time": 1200},   # Zone 2
                {"min": 140, "max": 150, "time": 900},    # Zone 3
                {"min": 150, "max": 160, "time": 600},    # Zone 4
                {"min": 160, "max": 170, "time": 300},    # Zone 5
                {"min": 170, "max": 180, "time": 0},      # Zone 6
                {"min": 180, "max": 200, "time": 0}       # Zone 7
            ]}
        ],
        "laps": [
            {
                "id": 1,
                "elapsed_time": 1800,
                "distance": 5000,
                "average_heartrate": 140
            },
            {
                "id": 2,
                "elapsed_time": 1800,
                "distance": 5000,
                "average_heartrate": 151
            }
        ]
    }


@pytest.fixture
def sample_activity_streams():
    """Sample activity time-series data"""
    # Generate 60 minutes of data (1 sample per second)
    time_data = list(range(3600))
    
    # Simulate heart rate that varies between zones
    heartrate_data = []
    for i in range(3600):
        if i < 1200:  # First 20 minutes - Zone 1
            hr = 115 + (i % 60) / 10
        elif i < 2400:  # Next 20 minutes - Zone 2
            hr = 135 + (i % 60) / 8
        else:  # Last 20 minutes - Zone 3/4
            hr = 155 + (i % 60) / 6
        heartrate_data.append(int(hr))
    
    return {
        "time": {"data": time_data},
        "heartrate": {"data": heartrate_data},
        "distance": {"data": [i * 2.78 for i in time_data]},  # ~10km/hour pace
        "altitude": {"data": [100 + (i % 300) / 10 for i in time_data]}
    }


@pytest.fixture
def mock_ai_response():
    """Sample OpenAI API response"""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4o",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": """## Personalized Training Recommendations

Based on your recent training data showing 70% Zone 1, 20% Zone 2, and 10% Zone 3 distribution:

### This Week's Focus
Your Zone 2 percentage is higher than the polarized target. Let's adjust:

**Monday - Recovery Run**
- Duration: 45 minutes
- Intensity: Zone 1 (conversational pace)
- Purpose: Active recovery

**Wednesday - Threshold Intervals**
- Warm-up: 15 min Zone 1
- Main: 4 x 8 min at Zone 3/4 border with 2 min Zone 1 recovery
- Cool-down: 10 min Zone 1
- Purpose: Improve lactate threshold

**Friday - Long Endurance**
- Duration: 90 minutes
- Intensity: Zone 1 with 2 x 10 min Zone 2 pickups
- Purpose: Build aerobic base

**Sunday - Optional Easy Activity**
- Duration: 30-60 minutes
- Intensity: Zone 1
- Activity: Run, bike, or row based on how you feel

### Key Points:
- Reduce Zone 2 time to meet polarized targets
- Maintain high volume in Zone 1
- Use Zone 3 work strategically for maximum benefit"""
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 250,
            "total_tokens": 400
        }
    }


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory for testing"""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "ai_recommendations").mkdir()
    return str(cache_dir)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv('STRAVA_CLIENT_ID', 'test_client_id')
    monkeypatch.setenv('STRAVA_CLIENT_SECRET', 'test_client_secret')
    monkeypatch.setenv('OPENAI_API_KEY', 'test_openai_key')
    monkeypatch.setenv('FLASK_SECRET_KEY', 'test_flask_secret')
    return monkeypatch


@pytest.fixture(autouse=True)
def prevent_network_calls(monkeypatch):
    """Prevent actual network calls during tests"""
    def mock_request(*args, **kwargs):
        raise RuntimeError("Network call attempted during test!")
    
    # Only patch if not already mocked
    if not hasattr(monkeypatch, '_network_patched'):
        monkeypatch.setattr('requests.get', mock_request)
        monkeypatch.setattr('requests.post', mock_request)
        monkeypatch.setattr('requests.put', mock_request)
        monkeypatch.setattr('requests.delete', mock_request)
        monkeypatch._network_patched = True


@pytest.fixture
def sample_workout_preferences():
    """Sample workout preferences data"""
    return """# Workout Preferences

## Equipment Available
- Peloton bike
- TRX suspension trainer  
- Running shoes (Nike Pegasus)
- Basic dumbbells (5-25 lbs)

## Goals
- Complete first half marathon in April
- Improve 10K time to under 50 minutes
- Build consistent training habit

## Constraints
- Maximum 60 minutes on weekdays
- Prefer morning workouts
- Mild knee issues - avoid high impact

## Training History
- Running for 2 years
- Completed several 5Ks
- Recently started cycling

## Preferences
- Enjoy interval training
- Like structured workouts with clear targets
- Prefer outdoor runs when weather permits
"""