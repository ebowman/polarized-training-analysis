# Volume Calculation Audit Report

## Summary of Discrepancy
There are THREE different volume calculations in `templates/index.html` that are producing inconsistent results:

1. **displaySummary** (Achievement card) - Shows 452 minutes
2. **displayCombinedChart** (Warning messages) - Calculates differently
3. **displayVolumeTracking** (Volume chart) - Shows 332 minutes

## Root Cause
The **120-minute discrepancy** appears to be caused by activities WITHOUT zone data being included in some calculations but excluded from others.

## Detailed Analysis

### 1. displaySummary Function (Line 1226)
```javascript
// Line 1243: Calculates total from ALL activities
const totalMinutes = filteredActivities.reduce((sum, a) => sum + a.duration_minutes, 0);
```
- **What it includes**: ALL activities in the time range
- **What it excludes**: Nothing - includes activities even without zone data
- **Result**: Shows 452 minutes (includes ~120 minutes of activities without zones)

### 2. displayCombinedChart Function (Line 1687)
```javascript
// Line 1725: Also calculates from all activities
const totalMinutes = filteredActivities.reduce((sum, a) => sum + a.duration_minutes, 0);
```
- **What it includes**: ALL activities in the time range
- **What it excludes**: Nothing initially, but zone calculations only count activities with zone data
- **Result**: Total minutes include all, but zone percentages only reflect activities with zones

### 3. displayVolumeTracking Function (Line 2409)
```javascript
// Line 2518: Only counts "polarized minutes" with zone data
rollingPolarizedMinutes += (dailyData[i].zone1Minutes + dailyData[i].zone2Minutes + dailyData[i].zone3Minutes);
```
- **What it includes**: Only activities with zone data (aerobic activities)
- **What it excludes**: 
  - Strength training (counted separately as `strengthMinutes`)
  - Activities without zone data
- **Result**: Shows 332 minutes of polarized training only

## Key Finding
The displayVolumeTracking function (line 2497-2498) logs activities without zones:
```javascript
if ((z1 + z2 + z3) === 0 && duration > 0) {
    console.log(`📊 Activity without zones: ${activity.name} (${duration}min) on ${activityDateStr}`);
}
```

## The Correct Approach
**displayVolumeTracking is CORRECT** - it properly separates:
- Polarized training minutes (activities with zone data): 332 min
- Ancillary/strength training: Tracked separately
- Activities without zones: Excluded from polarized total

## Recommendation
1. **displaySummary** should be modified to only count activities with zone data for the main achievement metric
2. **displayCombinedChart** should clarify that its total includes non-polarized activities
3. Consider showing a breakdown: "452 total (332 polarized + 120 unzoned/other)"

## Activities Without Zone Data
Based on the 120-minute discrepancy, there are likely activities in the system that:
- Have duration but no heart rate data
- Are not classified as strength training
- Could be activities like walking, yoga, or improperly imported workouts