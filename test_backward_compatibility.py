#!/usr/bin/env python3
"""
Test backward compatibility of Phase 2 refactoring
"""

import os
import sys
from datetime import datetime, timedelta

def test_without_sport_config():
    """Test that the system works without sport config"""
    # Disable sport config
    os.environ['USE_SPORT_CONFIG'] = 'false'
    
    print("Testing WITHOUT sport config...")
    
    # Test TrainingAnalyzer
    from training_analysis import TrainingAnalyzer
    
    analyzer = TrainingAnalyzer(max_hr=180, ftp=250, lthr=165)
    print("✅ TrainingAnalyzer instantiated successfully")
    
    # Test zone calculations
    hr_zone = analyzer._get_hr_zone(150)
    print(f"✅ HR zone calculation works: HR 150 -> Zone {hr_zone}")
    
    power_zone = analyzer._get_power_zone(200)
    print(f"✅ Power zone calculation works: 200W -> Zone {power_zone}")
    
    # Test AI recommendations
    try:
        from ai_recommendations import TrainingDataAnalyzer
        ai_analyzer = TrainingDataAnalyzer()
        print("✅ AI TrainingDataAnalyzer instantiated successfully")
        
        # Test adherence calculation
        score = ai_analyzer.calculate_adherence_score(80, 10, 10, 'polarized')
        print(f"✅ Adherence score calculation works: {score}")
    except Exception as e:
        print(f"❌ AI recommendations error: {e}")
    
    print("\n" + "="*50 + "\n")

def test_with_sport_config():
    """Test that the system works with sport config"""
    # Enable sport config
    os.environ['USE_SPORT_CONFIG'] = 'true'
    
    print("Testing WITH sport config...")
    
    # Create a sport config file if it doesn't exist
    if not os.path.exists('sport_config.json'):
        print("Creating default sport config...")
        from sport_config import create_default_config, ConfigValidator
        default_config = create_default_config()
        validator = ConfigValidator()
        config_dict = validator._config_to_dict(default_config)
        
        import json
        with open('sport_config.json', 'w') as f:
            json.dump(config_dict, f, indent=2)
        print("✅ Created default sport config")
    
    # Test TrainingAnalyzer with sport config
    from training_analysis import TrainingAnalyzer
    
    analyzer = TrainingAnalyzer(max_hr=180, ftp=250, lthr=165)
    print("✅ TrainingAnalyzer instantiated with sport config")
    
    # Test zone calculations with sport type
    hr_zone = analyzer._get_hr_zone(150, 'Run')
    print(f"✅ HR zone calculation with sport type: HR 150 (Run) -> Zone {hr_zone}")
    
    power_zone = analyzer._get_power_zone(200, 'Ride')
    print(f"✅ Power zone calculation with sport type: 200W (Ride) -> Zone {power_zone}")
    
    # Test activity analysis
    test_activity = {
        'id': 12345,
        'name': 'Test Ride',
        'start_date': datetime.now().isoformat(),
        'type': 'Ride',
        'elapsed_time': 3600,
        'has_heartrate': True,
        'average_heartrate': 140,
        'streams': None
    }
    
    analysis = analyzer.analyze_activity_hr(test_activity)
    if analysis:
        print(f"✅ Activity analysis works: {analysis.zone1_percent:.1f}% / {analysis.zone2_percent:.1f}% / {analysis.zone3_percent:.1f}%")
    else:
        print("⚠️  Activity analysis returned None (expected for simple test)")
    
    # Test AI with sport config
    try:
        from ai_recommendations import TrainingDataAnalyzer
        ai_analyzer = TrainingDataAnalyzer()
        print("✅ AI TrainingDataAnalyzer instantiated with sport config")
        
        # Test adherence with sport config targets
        score = ai_analyzer.calculate_adherence_score(80, 10, 10, 'polarized')
        print(f"✅ Adherence score with sport config: {score}")
    except Exception as e:
        print(f"❌ AI recommendations error: {e}")
    
    # Test web server zone calculations
    try:
        from web_server import get_zone_calculations
        zones = get_zone_calculations()
        print(f"✅ Web server zone calculations work")
        print(f"   - Training philosophy: {zones.get('training_philosophy', 'unknown')}")
        print(f"   - Zone targets: {zones.get('zone_targets', {})}")
    except Exception as e:
        print(f"❌ Web server error: {e}")

def main():
    """Run backward compatibility tests"""
    print("Phase 2 Backward Compatibility Tests")
    print("="*50)
    print()
    
    # Test 1: System works without sport config
    test_without_sport_config()
    
    # Test 2: System works with sport config
    test_with_sport_config()
    
    print("\nBackward compatibility test complete!")
    print("\nNOTE: All changes use feature flags (USE_SPORT_CONFIG env var)")
    print("      Set USE_SPORT_CONFIG=false to use legacy behavior")

if __name__ == '__main__':
    main()