#!/usr/bin/env python3
"""Test zone distribution extraction in config generator"""

from config_generator import ConfigGenerator

# Test the zone distribution extraction
test_cases = [
    # Test case 1: Explicit 80/10/10 format
    ("I follow a polarized approach with 80/10/10 zone distribution", {"1": 80.0, "2": 10.0, "3": 10.0}),
    
    # Test case 2: Zone percentages format
    ("Zone 1: 70%, Zone 2: 20%, Zone 3: 10%", {"1": 70.0, "2": 20.0, "3": 10.0}),
    
    # Test case 3: Philosophy-based default
    ("I use pyramidal training", {"1": 70.0, "2": 20.0, "3": 10.0}),
    
    # Test case 4: Threshold training
    ("My training is threshold-focused", {"1": 50.0, "2": 35.0, "3": 15.0}),
    
    # Test case 5: Default polarized
    ("I love cycling and running", {"1": 80.0, "2": 10.0, "3": 10.0}),
]

# Create a generator instance
generator = ConfigGenerator()

print("Testing zone distribution extraction:")
print("-" * 50)

for text, expected in test_cases:
    result = generator._extract_zone_distribution(text)
    passed = result == expected
    status = "✅" if passed else "❌"
    print(f"{status} Input: '{text}'")
    print(f"   Expected: {expected}")
    print(f"   Got: {result}")
    print()

# Test full config generation with zone distribution
print("\nTesting full config generation with sample preferences:")
print("-" * 50)

# Read the sample preferences
with open("workout_preferences_personal.md", "r") as f:
    prefs = f.read()

# Extract zone distribution
zone_dist = generator._extract_zone_distribution(prefs)
print(f"Extracted zone distribution: {zone_dist}")

# Check if it matches the expected 80/10/10
expected_dist = {"1": 80.0, "2": 10.0, "3": 10.0}
if zone_dist == expected_dist:
    print("✅ Zone distribution correctly extracted from workout_preferences_personal.md")
else:
    print("❌ Zone distribution extraction failed")
    print(f"   Expected: {expected_dist}")
    print(f"   Got: {zone_dist}")