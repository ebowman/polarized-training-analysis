# Training Zone Mapping Guide

## Understanding Different Zone Systems

There are multiple zone systems used in endurance training. This guide explains how they relate to each other and when to use each system.

## 1. Polarized Training Zones (Research-Based)

The NIH research defines **3 simple zones** for training distribution analysis:

| Polarized Zone | Purpose | Target Distribution |
|----------------|---------|-------------------|
| **Zone 1** | Low Intensity / Aerobic Base | **80%** of training time |
| **Zone 2** | Threshold / "Gray Zone" | **10%** of training time |
| **Zone 3** | High Intensity / VO2 Max | **10%** of training time |

## 2. Power Zones (Cycling - Peloton/FTP Based)

For cycling activities, we use **power zones** based on your Functional Threshold Power (FTP):

| Power Zone | % of FTP | Description | Maps to Polarized |
|------------|----------|-------------|-------------------|
| **Zone 1** | 0-55% | Active Recovery | Zone 1 |
| **Zone 2** | 55-75% | Endurance/Aerobic Base | Zone 1 |
| **Zone 3** | 75-90% | Tempo | Zone 1 |
| **Zone 4** | 90-105% | Lactate Threshold | Zone 2 |
| **Zone 5** | 105-120% | VO2 Max | Zone 3 |
| **Zone 6** | 120%+ | Anaerobic/Neuromuscular | Zone 3 |

### Peloton Power Zone Mapping
```
Polarized Zone 1 (80% target) = Power Zones 1-3 (0-90% FTP)
Polarized Zone 2 (10% target) = Power Zone 4 (90-105% FTP)  
Polarized Zone 3 (10% target) = Power Zones 5-6 (105%+ FTP)
```

## 3. Heart Rate Zones (Rowing/Running - HR Based)

For rowing and other activities without power data, we use **heart rate zones** based on your maximum HR (171 bpm):

| HR Zone | BPM Range | % of Max HR | Description | Maps to Polarized |
|---------|-----------|-------------|-------------|-------------------|
| **Zone 1** | 86-120 | 50-70% | Recovery/Easy | Zone 1 |
| **Zone 2** | 120-140 | 70-82% | Aerobic Base | Zone 1 |
| **Zone 3** | 140-149 | 82-87% | Aerobic Threshold | Zone 2 |
| **Zone 4** | 149-159 | 87-93% | Lactate Threshold | Zone 2 |
| **Zone 5** | 159+ | 93%+ | VO2 Max/Anaerobic | Zone 3 |

### Rowing Heart Rate Zone Mapping
```
Polarized Zone 1 (80% target) = HR Zones 1-2 (86-140 bpm)
Polarized Zone 2 (10% target) = HR Zones 3-4 (140-159 bpm)
Polarized Zone 3 (10% target) = HR Zone 5 (159+ bpm)
```

## 4. Activity-Specific Recommendations

### 🚴 **Cycling (Peloton) - Use Power Zones**
- **"Power Zone 2 Endurance Ride"** instead of "Zone 1 Easy Ride"
- **"Power Zone 4 Threshold Intervals"** instead of "Zone 2 Threshold"
- **"Power Zone 5 VO2 Max Intervals"** instead of "Zone 3 High Intensity"

Example: *"Power Zone 2-3 endurance ride for 90 minutes (65-85% FTP) to build aerobic base"*

### 🚣 **Rowing (Concept2) - Use Heart Rate Zones**
- **"HR Zone 2 Steady State"** instead of "Zone 1 Easy"
- **"HR Zone 4 Threshold Pieces"** instead of "Zone 2 Threshold"
- **"HR Zone 5 Intervals"** instead of "Zone 3 High Intensity"

Example: *"HR Zone 2 steady state for 45 minutes (120-140 bpm) for cross-training recovery"*

### 🏃 **Running - Use Heart Rate Zones**
Similar to rowing, running typically uses heart rate zones since most runners don't have power meters.

### 🏋️ **Strength Training - Different System**
Strength training uses different metrics:
- **RPE (Rate of Perceived Exertion)**: 1-10 scale
- **% of 1RM**: Percentage of one-rep maximum
- **Time-based**: Duration rather than intensity zones

## 5. Implementation in the Analysis Tool

### Automatic Zone Selection
The tool automatically chooses the appropriate zone system:

1. **Cycling Activities with Power Data** → Power Zones (FTP-based)
2. **Cycling Activities without Power** → Heart Rate Zones
3. **Rowing Activities** → Heart Rate Zones
4. **Running Activities** → Heart Rate Zones
5. **Other Activities** → Heart Rate Zones (fallback)

### Configuration
Your current settings:
- **Cycling FTP**: 301 watts (for power zone calculations)
- **Max Heart Rate**: 171 bpm (for HR zone calculations)
- **Rowing FTP**: Not set (will use HR zones for rowing)

### Display Logic
- **Polarized Analysis**: Always shows the 3-zone research breakdown for training distribution
- **Workout Recommendations**: Uses activity-specific zones (power for cycling, HR for rowing)
- **Individual Activities**: Shows appropriate zones based on available data

## 6. Practical Examples

### Polarized Training Distribution (Last 14 Days)
```
Zone 1 (Low): 75% [Target: 80%] ← Based on all activities combined
Zone 2 (Threshold): 15% [Target: 10%]
Zone 3 (High): 10% [Target: 10%]
```

### Specific Workout Recommendations
```
🚴 "60-min Power Zone 2 Endurance Ride (65-75% FTP)"
🚣 "45-min HR Zone 2 Steady State (120-140 bpm)"
🏋️ "30-min Functional Strength Circuit (RPE 6-7)"
```

## 7. Why This Approach?

1. **Scientific Accuracy**: Uses the most precise measurement available for each activity
2. **Practical Application**: Aligns with how athletes actually train
3. **Equipment-Specific**: Matches the tools and metrics you're already using
4. **Clear Communication**: Eliminates confusion between different zone systems

This way, you get polarized training analysis for overall planning, but specific power zone guidance for Peloton rides and heart rate zone guidance for rowing!