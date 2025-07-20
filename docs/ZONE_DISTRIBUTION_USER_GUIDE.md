# Zone Distribution Editor User Guide

## Overview

The Zone Distribution Editor allows you to customize how your training time is distributed across three intensity zones. This feature supports personalized training approaches and sport-specific adjustments to match your goals and physiological responses.

## Understanding Training Zones

### The 3-Zone Polarized Model

All zone distributions in the system map to a simplified 3-zone model:

1. **Zone 1 (Easy/Recovery)**: Below first ventilatory threshold (VT1/AeT)
   - Conversational pace
   - Fat oxidation dominant
   - Sustainable for hours

2. **Zone 2 (Moderate/Threshold)**: Between VT1 and VT2 (lactate threshold)
   - Comfortably hard
   - Mix of aerobic and anaerobic
   - Sustainable for 20-60 minutes

3. **Zone 3 (Hard/VO2max)**: Above VT2/AnT
   - Very hard to maximal
   - Primarily anaerobic
   - Sustainable for minutes

### Training Philosophies

**Polarized Training (80/10/10)**
- 80% in Zone 1 (easy)
- 10% in Zone 2 (threshold)
- 10% in Zone 3 (VO2max)
- Best for: Endurance athletes, high-volume training

**Pyramidal Training (70/20/10)**
- 70% in Zone 1 (easy)
- 20% in Zone 2 (threshold)
- 10% in Zone 3 (VO2max)
- Best for: Balanced approach, moderate volume

**Threshold Training (50/35/15)**
- 50% in Zone 1 (easy)
- 35% in Zone 2 (threshold)
- 15% in Zone 3 (VO2max)
- Best for: Time-crunched athletes, specific adaptations

## Using the Zone Distribution Editor

### Accessing the Editor

1. Navigate to Settings (`/settings`)
2. Click on the "Zone Distribution" tab
3. View current distributions for all sports

### Global vs Sport-Specific Settings

**Global Distribution**
- Applies to all sports by default
- Set your overall training philosophy
- Acts as the baseline for new sports

**Sport-Specific Distribution**
- Override global settings for individual sports
- Customize based on sport demands
- Examples:
  - Cycling: More polarized (85/5/10)
  - Running: More threshold work (70/20/10)
  - Swimming: Technique-focused (60/30/10)

### Making Changes

#### Visual Editor (Recommended)

1. **Using Sliders**:
   ```
   Zone 1: [====|--------] 80%
   Zone 2: [=|----------] 10%
   Zone 3: [=|----------] 10%
   Total: 100% ✓
   ```

2. **Preset Buttons**:
   - Click "Polarized" for 80/10/10
   - Click "Pyramidal" for 70/20/10
   - Click "Threshold" for 50/35/15

3. **Validation**:
   - Distributions must sum to 100%
   - Real-time validation shows errors
   - Save button enabled only when valid

#### JSON Editor (Advanced)

```json
{
  "zone_breakdown_percentage": {
    "1": 80.0,
    "2": 10.0,
    "3": 10.0
  }
}
```

### Sport-Specific Examples

**Ultra-Endurance Cycling**
```
Zone 1: 90%  // Maximum aerobic base
Zone 2: 5%   // Minimal threshold
Zone 3: 5%   // Occasional intensity
```

**Criterium Racing**
```
Zone 1: 60%  // Recovery between efforts
Zone 2: 20%  // Race pace simulation
Zone 3: 20%  // Sprint/attack practice
```

**Marathon Training**
```
Zone 1: 75%  // Easy miles
Zone 2: 20%  // Marathon pace work
Zone 3: 5%   // Speed development
```

## AI-Powered Configuration

### Writing Preferences

Create natural language preferences that the AI can understand:

```markdown
# My Training Preferences

## Current Fitness
- Cycling FTP: 301W
- Running LTHR: 155 bpm
- Training 10-15 hours/week

## Goals
- Improve cycling FTP by 20W
- Complete a sub-3 hour marathon
- Maintain fitness year-round

## Training Approach
I prefer a polarized approach for cycling (80% easy, minimal threshold work)
but need more tempo running for marathon preparation (70/20/10 split).

## Equipment
- Peloton bike for indoor cycling
- Garmin watch for running
- Concept2 rower for cross-training
```

### Generating Configuration

1. Click "Generate from Preferences"
2. Review the AI-generated configuration
3. Fine-tune zone distributions as needed
4. Save configuration

### Best Practices for AI Generation

**Be Specific**:
- Include current fitness metrics (FTP, LTHR, pace)
- Mention specific equipment
- State training philosophy preferences
- Include weekly volume ranges

**Use Keywords**:
- "Polarized", "pyramidal", "threshold"
- Sport names: "cycling", "running", "rowing"
- Equipment: "Peloton", "Concept2", "Zwift"
- Metrics: "FTP", "LTHR", "threshold pace"

## Monitoring Progress

### Zone Compliance

View your actual zone distribution vs targets:

```
Target:  [========|=|=] 80/10/10
Actual:  [=======|==|=] 72/18/10
         ↓ -8%  ↑ +8%  ✓
```

### Adjusting Based on Results

**Too Much Zone 1?**
- Increase Zone 2/3 targets
- Add more structured workouts
- Consider threshold focus period

**Too Much Zone 3?**
- Increase Zone 1 target
- Add more recovery days
- Monitor for overtraining

**Not Meeting Targets?**
- Review workout selection
- Check zone threshold accuracy
- Consider sport-specific adjustments

## Integration with Other Features

### Zone Mapping Guide
- View personalized zone ranges
- See watt/BPM values for each zone
- Understand how distributions affect training

### Workout Generator
- AI considers zone distributions
- Suggests workouts to meet targets
- Balances intensity across the week

### Progress Tracking
- Compare planned vs actual distributions
- Identify training patterns
- Optimize future planning

## Troubleshooting

### Common Issues

**"Distributions must sum to 100%"**
- Check for rounding errors
- Use the normalize button
- Adjust smallest value last

**"Sport not found"**
- Ensure sport exists in config
- Check exact spelling/case
- Add sport if missing

**"No AI provider available"**
- Configure OpenAI or Claude API key
- Check API key validity
- Ensure internet connection

### FAQ

**Q: Can I have different distributions for indoor vs outdoor cycling?**
A: Currently, distributions are per sport. Consider using the global setting for outdoor and sport-specific for indoor.

**Q: How often should I adjust distributions?**
A: Review monthly or with training phase changes. Major adjustments should align with periodization.

**Q: What if I don't follow any standard philosophy?**
A: Use custom distributions. The system supports any combination that sums to 100%.

**Q: Do distributions affect workout recommendations?**
A: Yes, the AI workout generator considers your target distributions when creating training plans.

## Advanced Usage

### Seasonal Adjustments

**Base Period**: 85/10/5 (maximize aerobic development)
**Build Period**: 75/15/10 (add race-specific intensity)
**Peak Period**: 70/15/15 (sharpen with high intensity)
**Recovery Period**: 90/5/5 (active recovery focus)

### Multi-Sport Considerations

For triathletes or multi-sport athletes:
- Set swimming more pyramidal (technique work)
- Keep cycling polarized (aerobic engine)
- Make running threshold-focused (race specific)

### API Integration

Programmatically update distributions:

```bash
# Update cycling to ultra-polarized
curl -X PUT http://localhost:5000/api/settings/zone-distribution/sport/Cycling \
  -H "Content-Type: application/json" \
  -d '{"zone_distribution": {"1": 90, "2": 5, "3": 5}}'

# Apply polarized philosophy to all sports
curl -X POST http://localhost:5000/api/settings/zone-distribution/apply-philosophy \
  -H "Content-Type: application/json" \
  -d '{"philosophy": "polarized", "apply_to": "all"}'
```

## Summary

The Zone Distribution Editor empowers you to:
- Customize training intensity distribution
- Adapt to different training phases
- Optimize sport-specific approaches
- Generate configurations from preferences
- Track compliance with targets

Remember: The best distribution is one that:
1. Matches your goals
2. Fits your available time
3. Allows consistent execution
4. Promotes long-term progress