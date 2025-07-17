# Zone Calculator API Documentation

## Overview

The `ZoneCalculator` class provides a unified interface for all zone calculations in the PolarFlow application. It consolidates duplicate zone calculation logic and provides a clean API for zone percentage calculations, zone mapping, and sport-specific calculations.

## Key Features

- **Unified zone calculation logic** - Single source of truth for all zone calculations
- **7-zone to 3-zone polarized mapping** - Seamless conversion between detailed and simplified models
- **Sport-specific zone calculations** - Integration with sport configuration system
- **Strategy pattern implementation** - Extensible architecture for different calculation methods
- **Full backward compatibility** - Drop-in replacement for existing code patterns
- **Comprehensive testing** - Full test coverage with edge cases

## Quick Start

```python
from zone_calculator import ZoneCalculator

# Initialize with thresholds
calc = ZoneCalculator(max_hr=180, lthr=160, ftp=250)

# Calculate zones
hr_zones = calc.calculate_hr_zones()
power_zones = calc.calculate_power_zones()

# Get zone for specific values
hr_zone = calc.get_hr_zone(150)  # Returns zone number (1-7)
power_zone = calc.get_power_zone(200)  # Returns zone number (1-7)

# Map to polarized zones
polarized_zone = calc.map_to_polarized_zone(hr_zone)  # Returns 1, 2, or 3
```

## Core Classes

### ZoneCalculator

The main class for zone calculations.

#### Constructor

```python
ZoneCalculator(max_hr: Optional[int] = None, 
               lthr: Optional[int] = None, 
               ftp: Optional[int] = None)
```

**Parameters:**
- `max_hr`: Maximum heart rate (defaults to `MAX_HEART_RATE` env var or 180)
- `lthr`: Lactate threshold heart rate (defaults to `AVERAGE_FTP_HR` env var or 0)
- `ftp`: Functional threshold power (defaults to `FTP` env var or 250)

**Note:** If `lthr` is 0, the calculator will use a simplified 3-zone model based on max HR.

#### Methods

##### Zone Calculation

```python
calculate_hr_zones(sport_type: Optional[str] = None) -> List[ZoneBoundary]
```
Calculate heart rate zones. Returns 7 zones when LTHR is available, 3 zones when using max HR fallback.

```python
calculate_power_zones(sport_type: Optional[str] = None) -> List[ZoneBoundary]
```
Calculate power zones (always returns 7 zones using Coggan model).

##### Zone Lookup

```python
get_hr_zone(hr: int, sport_type: Optional[str] = None) -> int
```
Get heart rate zone number (1-7 or 1-3 depending on model) for a given heart rate.

```python
get_power_zone(power: int, sport_type: Optional[str] = None) -> int
```
Get power zone number (1-7) for a given power value.

##### Zone Mapping

```python
map_to_polarized_zone(zone_7: int, 
                     metric_type: str = "heart_rate", 
                     sport_type: Optional[str] = None) -> int
```
Map 7-zone model to 3-zone polarized model.

**Standard mapping:**
- Zones 1-2 → Polarized Zone 1 (Low intensity)
- Zones 3-4 → Polarized Zone 2 (Threshold)
- Zones 5-7 → Polarized Zone 3 (High intensity)

##### Percentage Calculations

```python
calculate_zone_percentages(zone_times: Dict[int, float]) -> Dict[int, float]
```
Calculate zone percentages from zone times (in seconds).

```python
calculate_polarized_percentages(zone_times: Dict[int, float], 
                               metric_type: str = "heart_rate",
                               sport_type: Optional[str] = None) -> Dict[int, float]
```
Calculate polarized zone percentages (3-zone model) from 7-zone times.

##### Training Analysis

```python
get_zone_distribution_targets(philosophy: str = "polarized") -> Dict[int, float]
```
Get target zone distribution percentages.

**Supported philosophies:**
- `"polarized"`: 80% Zone 1, 10% Zone 2, 10% Zone 3
- `"pyramidal"`: 70% Zone 1, 20% Zone 2, 10% Zone 3
- `"threshold"`: 60% Zone 1, 30% Zone 2, 10% Zone 3

```python
calculate_zone_deviations(actual_percentages: Dict[int, float], 
                         philosophy: str = "polarized") -> Dict[int, float]
```
Calculate deviations from target zone distribution (positive = excess, negative = deficit).

```python
calculate_adherence_score(actual_percentages: Dict[int, float],
                         philosophy: str = "polarized") -> float
```
Calculate adherence score (0-100) based on deviation from targets.

##### Threshold Management

```python
update_thresholds(max_hr: Optional[int] = None, 
                 lthr: Optional[int] = None,
                 ftp: Optional[int] = None)
```
Update threshold values and sync with sport configuration if available.

### ZoneBoundary

Represents a zone boundary with all relevant information.

```python
@dataclass
class ZoneBoundary:
    lower: float           # Lower boundary value
    upper: float           # Upper boundary value
    name: str             # Zone name (e.g., "Tempo", "Threshold")
    number: int           # Zone number (1-7)
    polarized_zone: int   # Polarized zone mapping (1-3)
```

### Strategy Classes

The calculator uses strategy pattern for different calculation methods:

#### HeartRateZoneStrategy
7-zone LTHR-based model:
- Zone 1: Recovery (<81% LTHR)
- Zone 2: Aerobic (81-89% LTHR)
- Zone 3: Tempo (90-93% LTHR)
- Zone 4: Threshold (94-99% LTHR)
- Zone 5: VO2max (100-102% LTHR)
- Zone 6: Anaerobic (103-106% LTHR)
- Zone 7: Neuromuscular (>106% LTHR)

#### PowerZoneStrategy
7-zone Coggan model:
- Zone 1: Recovery (<55% FTP)
- Zone 2: Endurance (56-75% FTP)
- Zone 3: Tempo (76-90% FTP)
- Zone 4: Threshold (91-105% FTP)
- Zone 5: VO2max (106-120% FTP)
- Zone 6: Anaerobic (121-150% FTP)
- Zone 7: Neuromuscular (>150% FTP)

#### SimpleHeartRateZoneStrategy
3-zone max HR model (fallback):
- Zone 1: Low (<82% max HR)
- Zone 2: Threshold (82-87% max HR)
- Zone 3: High (>87% max HR)

## Utility Functions

### Factory Function

```python
create_zone_calculator(**kwargs) -> ZoneCalculator
```
Factory function to create a ZoneCalculator instance with keyword arguments.

### Stream Calculation

```python
calculate_zone_percentages_from_stream(stream_data: List[float], 
                                      threshold: float,
                                      calculator: Optional[ZoneCalculator] = None,
                                      metric_type: str = "heart_rate",
                                      sport_type: Optional[str] = None) -> Dict[int, float]
```
Calculate zone percentages from a stream of data (HR or power values).

## Integration with Sport Configuration

The zone calculator integrates seamlessly with the sport configuration system:

```python
# Sport-specific zone calculations
calc = ZoneCalculator()
zones = calc.calculate_hr_zones(sport_type="Run")
zone_number = calc.get_hr_zone(150, sport_type="VirtualRide")
```

When sport configuration is available, the calculator will:
1. Use sport-specific zone definitions
2. Apply custom zone boundaries
3. Use sport-specific polarized zone mappings
4. Integrate with user profile thresholds

## Backward Compatibility

The zone calculator is designed to be a drop-in replacement for existing code patterns:

### Replacing TrainingAnalyzer zone calculations

**Old pattern:**
```python
# In TrainingAnalyzer._get_hr_zone()
if hr <= self.hr_zones.zone1_max:
    return 1
elif hr <= self.hr_zones.zone2_max:
    return 2
# ... more conditions
```

**New pattern:**
```python
calc = ZoneCalculator(lthr=self.lthr)
zone = calc.get_hr_zone(hr, sport_type)
```

### Replacing duplicate percentage calculations

**Old pattern:**
```python
# Multiple locations with similar code
zone1_percent = zone1_seconds / total_seconds * 100
zone2_percent = zone2_seconds / total_seconds * 100
zone3_percent = zone3_seconds / total_seconds * 100
```

**New pattern:**
```python
calc = ZoneCalculator()
zone_times = {1: zone1_seconds, 2: zone2_seconds, 3: zone3_seconds}
percentages = calc.calculate_zone_percentages(zone_times)
```

### Replacing zone mapping logic

**Old pattern:**
```python
# In _map_to_3zone()
if zone_7 <= 2:
    return 1
elif zone_7 <= 4:
    return 2
else:
    return 3
```

**New pattern:**
```python
calc = ZoneCalculator()
polarized_zone = calc.map_to_polarized_zone(zone_7, metric_type, sport_type)
```

## Usage Examples

### Basic Zone Calculation

```python
from zone_calculator import ZoneCalculator

# Initialize calculator
calc = ZoneCalculator(lthr=160, ftp=250)

# Calculate zones
hr_zones = calc.calculate_hr_zones()
power_zones = calc.calculate_power_zones()

# Print zone information
for zone in hr_zones:
    print(f"HR {zone.name}: {zone.lower:.0f}-{zone.upper:.0f} bpm (Polarized Zone {zone.polarized_zone})")

for zone in power_zones:
    print(f"Power {zone.name}: {zone.lower:.0f}-{zone.upper:.0f}W (Polarized Zone {zone.polarized_zone})")
```

### Activity Analysis

```python
from zone_calculator import ZoneCalculator
import numpy as np

# Sample activity data
hr_data = [120, 135, 145, 155, 160, 165, 170, 175]  # Heart rate stream
time_data = [0, 60, 120, 180, 240, 300, 360, 420]   # Time in seconds

calc = ZoneCalculator(lthr=160)

# Calculate time in each zone
zone_times = {i: 0 for i in range(1, 8)}
for i, hr in enumerate(hr_data[:-1]):
    duration = time_data[i+1] - time_data[i]
    zone = calc.get_hr_zone(hr)
    zone_times[zone] += duration

# Calculate zone percentages
zone_percentages = calc.calculate_zone_percentages(zone_times)
polarized_percentages = calc.calculate_polarized_percentages(zone_times)

print("7-Zone Distribution:")
for zone, percent in zone_percentages.items():
    if percent > 0:
        print(f"  Zone {zone}: {percent:.1f}%")

print("\nPolarized Distribution:")
for zone, percent in polarized_percentages.items():
    print(f"  Zone {zone}: {percent:.1f}%")
```

### Training Analysis

```python
from zone_calculator import ZoneCalculator

calc = ZoneCalculator()

# Sample training data (polarized zone percentages)
actual_distribution = {1: 75.0, 2: 15.0, 3: 10.0}

# Analyze adherence to polarized training
targets = calc.get_zone_distribution_targets("polarized")
deviations = calc.calculate_zone_deviations(actual_distribution, "polarized")
adherence_score = calc.calculate_adherence_score(actual_distribution, "polarized")

print(f"Targets: {targets}")
print(f"Actual: {actual_distribution}")
print(f"Deviations: {deviations}")
print(f"Adherence Score: {adherence_score:.1f}/100")

# Recommendations based on deviations
for zone, deviation in deviations.items():
    if deviation > 5:
        print(f"Reduce Zone {zone} by {deviation:.1f}%")
    elif deviation < -5:
        print(f"Increase Zone {zone} by {abs(deviation):.1f}%")
```

### Sport-Specific Calculations

```python
from zone_calculator import ZoneCalculator

calc = ZoneCalculator()

# Different sports may have different zone calculations
running_zone = calc.get_hr_zone(150, sport_type="Run")
cycling_zone = calc.get_power_zone(200, sport_type="Ride")

# Sport-specific zone boundaries
running_zones = calc.calculate_hr_zones(sport_type="Run")
cycling_zones = calc.calculate_power_zones(sport_type="Ride")

print(f"Running HR 150: Zone {running_zone}")
print(f"Cycling 200W: Zone {cycling_zone}")
```

## Testing

The zone calculator includes comprehensive tests covering:

- Basic zone calculations
- Backward compatibility
- Sport-specific calculations
- Edge cases and error handling
- Performance testing

Run tests with:

```bash
python -m pytest test_zone_calculator.py -v
```

## Performance Considerations

The zone calculator is optimized for performance:

- **Lazy initialization**: Strategies are created only when needed
- **Caching**: Zone boundaries are calculated once and reused
- **Efficient algorithms**: O(1) zone lookups for most operations
- **Memory efficient**: Minimal object creation during calculations

## Error Handling

The calculator includes robust error handling:

- **Invalid threshold values**: Graceful fallback to defaults
- **Missing sport configuration**: Automatic fallback to standard calculations
- **Invalid zone numbers**: Sensible defaults (zone 1 for low values, max zone for high values)
- **Empty data**: Returns appropriate empty results

## Migration Guide

### From TrainingAnalyzer

1. Replace `TrainingAnalyzer._get_hr_zone()` calls:
   ```python
   # Old
   zone = self._get_hr_zone(hr, sport_type)
   
   # New
   calc = ZoneCalculator(lthr=self.lthr)
   zone = calc.get_hr_zone(hr, sport_type)
   ```

2. Replace zone percentage calculations:
   ```python
   # Old
   zone1_percent = zone1_seconds / total_seconds * 100
   
   # New
   calc = ZoneCalculator()
   percentages = calc.calculate_zone_percentages(zone_times)
   zone1_percent = percentages[1]
   ```

3. Replace polarized zone mapping:
   ```python
   # Old
   polarized_zone = self._map_to_3zone(zone_7, sport_type)
   
   # New
   calc = ZoneCalculator()
   polarized_zone = calc.map_to_polarized_zone(zone_7, "heart_rate", sport_type)
   ```

### From ai_recommendations.py

1. Replace zone distribution calculations:
   ```python
   # Old
   zone1_percent, zone2_percent, zone3_percent, total_minutes = \
       self.calculate_zone_distribution(recent_activities)
   
   # New
   calc = ZoneCalculator()
   zone_times = {1: zone1_time, 2: zone2_time, 3: zone3_time}
   percentages = calc.calculate_polarized_percentages(zone_times)
   ```

2. Replace adherence scoring:
   ```python
   # Old
   adherence_score = self.calculate_adherence_score(
       zone1_percent, zone2_percent, zone3_percent, training_approach
   )
   
   # New
   calc = ZoneCalculator()
   adherence_score = calc.calculate_adherence_score(percentages, training_approach)
   ```

## Extension Points

The zone calculator is designed for extensibility:

### Adding New Zone Models

```python
class CustomZoneStrategy(ZoneCalculationStrategy):
    def calculate_zones(self, threshold: float, sport_type: Optional[str] = None) -> List[ZoneBoundary]:
        # Custom zone calculation logic
        pass
    
    def get_zone_number(self, value: float, threshold: float, sport_type: Optional[str] = None) -> int:
        # Custom zone lookup logic
        pass

# Register strategy
calc._zone_strategies["custom"] = CustomZoneStrategy()
```

### Adding New Metrics

The calculator can be extended to support new metrics (e.g., pace, cadence):

```python
class PaceZoneStrategy(ZoneCalculationStrategy):
    def calculate_zones(self, threshold: float, sport_type: Optional[str] = None) -> List[ZoneBoundary]:
        # Pace-based zone calculation
        pass
```

### Sport-Specific Customizations

Integration with sport configuration allows for:
- Custom zone boundaries per sport
- Sport-specific polarized zone mappings
- Dynamic threshold selection based on sport type

## Future Enhancements

Planned enhancements include:

1. **Real-time zone tracking**: Live zone calculations during workouts
2. **Machine learning integration**: Adaptive zone boundaries based on performance
3. **Multi-metric zones**: Combining HR, power, and pace for hybrid zones
4. **Seasonal adjustments**: Automatic threshold updates based on fitness trends
5. **Recovery-aware zones**: Zone adjustments based on recovery metrics

## Conclusion

The `ZoneCalculator` provides a robust, extensible, and backward-compatible solution for all zone calculations in the PolarFlow application. It eliminates code duplication, provides a clean API, and integrates seamlessly with the existing codebase while enabling future enhancements.