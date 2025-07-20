# Zone Distribution Examples & Best Practices

## Sport-Specific Distribution Examples

### Cycling

#### Road Racing (Polarized)
```json
{
  "zone_breakdown_percentage": {
    "1": 80.0,  // Base endurance miles
    "2": 10.0,  // Threshold/Sweet spot
    "3": 10.0   // VO2max/Sprints
  }
}
```
**Use case**: Long road races, grand tours, century rides
**Benefits**: Maximizes aerobic capacity while maintaining top-end power

#### Criterium Racing (Balanced)
```json
{
  "zone_breakdown_percentage": {
    "1": 65.0,  // Recovery between efforts
    "2": 20.0,  // Race simulation
    "3": 15.0   // Sprint/attack practice
  }
}
```
**Use case**: Short, intense races with repeated surges
**Benefits**: Prepares for variable power demands

#### Time Trial Specialist (Threshold)
```json
{
  "zone_breakdown_percentage": {
    "1": 55.0,  // Aerobic support
    "2": 35.0,  // TT-specific work
    "3": 10.0   // Power development
  }
}
```
**Use case**: 40K TT, hour record attempts
**Benefits**: Maximizes threshold power

#### Ultra-Endurance (Super Polarized)
```json
{
  "zone_breakdown_percentage": {
    "1": 90.0,  // Ultra-distance pace
    "2": 5.0,   // Tempo efforts
    "3": 5.0    // Minimal intensity
  }
}
```
**Use case**: 200+ mile events, multi-day tours
**Benefits**: Builds massive aerobic base, prevents burnout

### Running

#### Marathon Training (Pyramidal)
```json
{
  "zone_breakdown_percentage": {
    "1": 70.0,  // Easy miles
    "2": 25.0,  // Marathon pace/tempo
    "3": 5.0    // Speed maintenance
  }
}
```
**Use case**: Sub-3 to sub-4 hour marathons
**Benefits**: Builds endurance with race-specific pace

#### 5K/10K Racing (Balanced Intensity)
```json
{
  "zone_breakdown_percentage": {
    "1": 60.0,  // Recovery/easy runs
    "2": 25.0,  // Threshold runs
    "3": 15.0   // Track intervals
  }
}
```
**Use case**: Short distance racing
**Benefits**: Develops speed and lactate tolerance

#### Ultra Running (Extreme Polarized)
```json
{
  "zone_breakdown_percentage": {
    "1": 85.0,  // Time on feet
    "2": 10.0,  // Hill work
    "3": 5.0    // Power hiking
  }
}
```
**Use case**: 50K to 100-mile races
**Benefits**: Maximizes fat oxidation and durability

### Rowing

#### 2K Racing (Power Focus)
```json
{
  "zone_breakdown_percentage": {
    "1": 60.0,  // UT2 steady state
    "2": 25.0,  // UT1/AT work
    "3": 15.0   // Race pace/power
  }
}
```
**Use case**: Competitive 2000m racing
**Benefits**: Builds power for 6-8 minute efforts

#### Endurance Rowing (Traditional)
```json
{
  "zone_breakdown_percentage": {
    "1": 75.0,  // Long steady state
    "2": 20.0,  // AT pieces
    "3": 5.0    // Power strokes
  }
}
```
**Use case**: Head races, team boats
**Benefits**: Classic rowing distribution

### Swimming

#### Distance Swimming (Aerobic)
```json
{
  "zone_breakdown_percentage": {
    "1": 70.0,  // Aerobic sets
    "2": 20.0,  // CSS work
    "3": 10.0   // Speed work
  }
}
```
**Use case**: 800m/1500m pool, open water
**Benefits**: Builds swimming economy

#### Sprint Swimming (Anaerobic)
```json
{
  "zone_breakdown_percentage": {
    "1": 50.0,  // Technique/recovery
    "2": 30.0,  // Lactate production
    "3": 20.0   // Sprint sets
  }
}
```
**Use case**: 50m/100m events
**Benefits**: Develops speed and power

### Triathlon

#### Ironman (Volume-Based)
```json
{
  "zone_breakdown_percentage": {
    "1": 85.0,  // Aerobic efficiency
    "2": 10.0,  // Race pace work
    "3": 5.0    // Maintenance
  }
}
```
**Use case**: Full distance triathlon
**Benefits**: Prevents overtraining across three sports

#### Olympic Distance (Intensity)
```json
{
  "zone_breakdown_percentage": {
    "1": 65.0,  // Base fitness
    "2": 25.0,  // Race pace
    "3": 10.0   // Speed work
  }
}
```
**Use case**: 1.5/40/10K racing
**Benefits**: Balances speed with endurance

## Seasonal Progression Examples

### Base Phase → Race Phase Evolution

#### Winter Base (December-February)
```json
{
  "zone_breakdown_percentage": {
    "1": 85.0,
    "2": 10.0,
    "3": 5.0
  }
}
```

#### Early Build (March-April)
```json
{
  "zone_breakdown_percentage": {
    "1": 75.0,
    "2": 15.0,
    "3": 10.0
  }
}
```

#### Late Build (May-June)
```json
{
  "zone_breakdown_percentage": {
    "1": 70.0,
    "2": 20.0,
    "3": 10.0
  }
}
```

#### Race Phase (July-August)
```json
{
  "zone_breakdown_percentage": {
    "1": 65.0,
    "2": 20.0,
    "3": 15.0
  }
}
```

#### Transition (September-November)
```json
{
  "zone_breakdown_percentage": {
    "1": 90.0,
    "2": 5.0,
    "3": 5.0
  }
}
```

## Special Populations

### Masters Athletes (40+)
```json
{
  "zone_breakdown_percentage": {
    "1": 75.0,  // More recovery needed
    "2": 15.0,  // Quality over quantity
    "3": 10.0   // Maintain power
  }
}
```
**Rationale**: Longer recovery times, focus on quality

### Junior Athletes (Under 18)
```json
{
  "zone_breakdown_percentage": {
    "1": 80.0,  // Aerobic development
    "2": 15.0,  // Technique focus
    "3": 5.0    // Limited high intensity
  }
}
```
**Rationale**: Build base, prevent burnout

### Rehabilitation/Return from Injury
```json
{
  "zone_breakdown_percentage": {
    "1": 90.0,  // Gentle progression
    "2": 8.0,   // Controlled efforts
    "3": 2.0    // Minimal intensity
  }
}
```
**Rationale**: Safe return to training

## Common Mistakes to Avoid

### ❌ The "No Pain, No Gain" Distribution
```json
{
  "zone_breakdown_percentage": {
    "1": 30.0,  // Too little easy
    "2": 40.0,  // Too much moderate
    "3": 30.0   // Too much hard
  }
}
```
**Problem**: Leads to overtraining and plateau

### ❌ The "Gray Zone" Distribution
```json
{
  "zone_breakdown_percentage": {
    "1": 40.0,
    "2": 50.0,  // Stuck in the middle
    "3": 10.0
  }
}
```
**Problem**: Not easy enough to recover, not hard enough to adapt

### ❌ The "Weekend Warrior" Distribution
```json
{
  "zone_breakdown_percentage": {
    "1": 95.0,  // All easy during week
    "2": 0.0,
    "3": 5.0    // One hard weekend ride
  }
}
```
**Problem**: Insufficient stimulus for improvement

## Best Practices

### 1. Match Distribution to Goals
- **Endurance events**: More Zone 1 (75-85%)
- **Middle distance**: Balanced approach (65-75% Zone 1)
- **Short/power events**: More intensity (50-65% Zone 1)

### 2. Consider Training History
- **Beginners**: Start with 80/15/5 or more conservative
- **Intermediate**: Standard distributions work well
- **Advanced**: Can handle more intensity (but often don't need it)

### 3. Adjust for Life Stress
- **High stress periods**: Increase Zone 1 percentage
- **Low stress periods**: Can handle standard distributions
- **Competition periods**: May temporarily increase Zone 3

### 4. Monitor and Adjust
- Track actual vs target weekly
- Adjust if consistently missing targets
- Consider why targets aren't being met

### 5. Sport-Specific Considerations
- **Power sports**: May need more Zone 3
- **Ultra-endurance**: Maximize Zone 1
- **Technical sports**: Factor in skill work (usually Zone 1)

## Integration with Training Plans

### Weekly Distribution Example

**Target**: 80/10/10 over 10 hours

**Monday**: Rest
**Tuesday**: 1hr Zone 1 (easy run)
**Wednesday**: 1hr with 20min Zone 2 (tempo)
**Thursday**: 1hr Zone 1 (easy bike)
**Friday**: 45min Zone 1 (recovery)
**Saturday**: 3hr Zone 1 (long ride)
**Sunday**: 2hr Zone 1 + 15min Zone 3 (intervals)

**Weekly Total**:
- Zone 1: 7.75 hours (77.5%)
- Zone 2: 0.33 hours (3.3%)
- Zone 3: 0.25 hours (2.5%)
- Unmeasured: 1.67 hours (16.7%)

**Note**: Perfect distribution is rarely achieved weekly but should average out monthly.

## Conclusion

Zone distribution is a powerful tool for optimizing training, but it's not one-size-fits-all. Use these examples as starting points, then adjust based on:
- Your response to training
- Available time
- Specific goals
- Life circumstances
- Enjoyment and sustainability

Remember: The best distribution is one you can execute consistently over time.