#!/usr/bin/env python
"""
Training Analysis Module

Analyzes training data based on polarized training approach from:
"Training Intensity Distribution in Endurance Athletes: Are We Asking the Right Questions?"
https://pmc.ncbi.nlm.nih.gov/articles/PMC4621419/

This module calculates training intensity zones and assesses adherence to 
polarized training methodology (approximately 80% low intensity, 10-15% threshold, 5-10% high intensity).
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from dotenv import load_dotenv

load_dotenv()

@dataclass
class TrainingZones:
    """Training intensity zones based on heart rate"""
    zone1_max: int  # Low intensity upper limit
    zone2_max: int  # Threshold zone upper limit
    zone3_min: int  # High intensity lower limit
    max_hr: int     # Maximum heart rate
    
    @classmethod
    def from_max_hr(cls, max_hr: int) -> 'TrainingZones':
        """Create zones from maximum heart rate using standard percentages"""
        return cls(
            zone1_max=int(max_hr * 0.82),  # ~82% max HR for aerobic threshold
            zone2_max=int(max_hr * 0.87),  # ~87% max HR for anaerobic threshold
            zone3_min=int(max_hr * 0.87),  # Above anaerobic threshold
            max_hr=max_hr
        )

@dataclass
class PowerZones:
    """Training intensity zones based on power (FTP)"""
    zone1_max: int  # Low intensity upper limit (65% FTP)
    zone2_max: int  # Threshold zone upper limit (88% FTP)
    zone3_min: int  # High intensity lower limit (88% FTP)
    ftp: int        # Functional Threshold Power
    
    @classmethod
    def from_ftp(cls, ftp: int) -> 'PowerZones':
        """Create zones from FTP"""
        return cls(
            zone1_max=int(ftp * 0.65),  # 65% FTP for aerobic base
            zone2_max=int(ftp * 0.88),  # 88% FTP for threshold
            zone3_min=int(ftp * 0.88),  # Above threshold
            ftp=ftp
        )

@dataclass
class ActivityAnalysis:
    """Analysis results for a single activity"""
    activity_id: int
    name: str
    date: str
    duration_minutes: int
    zone1_minutes: int
    zone2_minutes: int
    zone3_minutes: int
    zone1_percent: float
    zone2_percent: float
    zone3_percent: float
    average_hr: Optional[int] = None
    average_power: Optional[int] = None

class WorkoutType(Enum):
    """Types of recommended workouts"""
    EASY_AEROBIC = "easy_aerobic"
    LONG_AEROBIC = "long_aerobic" 
    TEMPO = "tempo"
    THRESHOLD = "threshold"
    INTERVALS = "intervals"
    RECOVERY = "recovery"

@dataclass
class WorkoutRecommendation:
    """Workout recommendation with specific details"""
    workout_type: WorkoutType
    primary_zone: int
    duration_minutes: int
    description: str
    structure: str
    reasoning: str
    priority: str  # "high", "medium", "low"

@dataclass
class TrainingDistribution:
    """Training intensity distribution analysis"""
    total_activities: int
    total_minutes: int
    zone1_minutes: int
    zone2_minutes: int
    zone3_minutes: int
    zone1_percent: float
    zone2_percent: float
    zone3_percent: float
    adherence_score: float
    recommendations: List[str]

class TrainingAnalyzer:
    """Analyzes training data for adherence to polarized training approach"""
    
    def __init__(self, max_hr: Optional[int] = None, ftp: Optional[int] = None):
        self.max_hr = max_hr or int(os.getenv("MAX_HEART_RATE", "180"))
        self.ftp = ftp or int(os.getenv("FTP", "250"))
        
        self.hr_zones = TrainingZones.from_max_hr(self.max_hr)
        self.power_zones = PowerZones.from_ftp(self.ftp)
        
        # Target distribution based on polarized training (80/10/10 approach)
        self.target_zone1_percent = 80.0
        self.target_zone2_percent = 10.0
        self.target_zone3_percent = 10.0
    
    def analyze_activity_hr(self, activity: Dict) -> Optional[ActivityAnalysis]:
        """Analyze single activity based on heart rate data"""
        streams = activity.get('streams')
        if not streams or 'heartrate' not in streams:
            return None
        
        hr_data = streams['heartrate']['data']
        time_data = streams.get('time', {}).get('data', [])
        
        if not hr_data or not time_data:
            return None
        
        # Calculate time in each zone
        zone1_seconds = 0
        zone2_seconds = 0
        zone3_seconds = 0
        
        for i, hr in enumerate(hr_data):
            if i < len(time_data) - 1:
                time_delta = time_data[i + 1] - time_data[i]
            else:
                time_delta = 1  # Default 1 second for last point
            
            if hr <= self.hr_zones.zone1_max:
                zone1_seconds += time_delta
            elif hr <= self.hr_zones.zone2_max:
                zone2_seconds += time_delta
            else:
                zone3_seconds += time_delta
        
        total_seconds = zone1_seconds + zone2_seconds + zone3_seconds
        if total_seconds == 0:
            return None
        
        zone1_minutes = zone1_seconds / 60
        zone2_minutes = zone2_seconds / 60
        zone3_minutes = zone3_seconds / 60
        total_minutes = total_seconds / 60
        
        return ActivityAnalysis(
            activity_id=activity['id'],
            name=activity['name'],
            date=activity['start_date'],
            duration_minutes=int(total_minutes),
            zone1_minutes=int(zone1_minutes),
            zone2_minutes=int(zone2_minutes),
            zone3_minutes=int(zone3_minutes),
            zone1_percent=zone1_seconds / total_seconds * 100,
            zone2_percent=zone2_seconds / total_seconds * 100,
            zone3_percent=zone3_seconds / total_seconds * 100,
            average_hr=int(np.mean(hr_data)) if hr_data else None
        )
    
    def analyze_activity_power(self, activity: Dict) -> Optional[ActivityAnalysis]:
        """Analyze single activity based on power data"""
        streams = activity.get('streams')
        if not streams or 'watts' not in streams:
            return None
        
        power_data = streams['watts']['data']
        time_data = streams.get('time', {}).get('data', [])
        
        if not power_data or not time_data:
            return None
        
        # Calculate time in each zone
        zone1_seconds = 0
        zone2_seconds = 0
        zone3_seconds = 0
        
        for i, power in enumerate(power_data):
            if i < len(time_data) - 1:
                time_delta = time_data[i + 1] - time_data[i]
            else:
                time_delta = 1  # Default 1 second for last point
            
            if power <= self.power_zones.zone1_max:
                zone1_seconds += time_delta
            elif power <= self.power_zones.zone2_max:
                zone2_seconds += time_delta
            else:
                zone3_seconds += time_delta
        
        total_seconds = zone1_seconds + zone2_seconds + zone3_seconds
        if total_seconds == 0:
            return None
        
        zone1_minutes = zone1_seconds / 60
        zone2_minutes = zone2_seconds / 60
        zone3_minutes = zone3_seconds / 60
        total_minutes = total_seconds / 60
        
        return ActivityAnalysis(
            activity_id=activity['id'],
            name=activity['name'],
            date=activity['start_date'],
            duration_minutes=int(total_minutes),
            zone1_minutes=int(zone1_minutes),
            zone2_minutes=int(zone2_minutes),
            zone3_minutes=int(zone3_minutes),
            zone1_percent=zone1_seconds / total_seconds * 100,
            zone2_percent=zone2_seconds / total_seconds * 100,
            zone3_percent=zone3_seconds / total_seconds * 100,
            average_power=int(np.mean(power_data)) if power_data else None
        )
    
    def analyze_activities(self, activities: List[Dict], use_power: bool = False) -> List[ActivityAnalysis]:
        """Analyze multiple activities"""
        analyses = []
        
        for activity in activities:
            if use_power:
                analysis = self.analyze_activity_power(activity)
            else:
                analysis = self.analyze_activity_hr(activity)
            
            if analysis:
                analyses.append(analysis)
        
        return analyses
    
    def calculate_training_distribution(self, analyses: List[ActivityAnalysis]) -> TrainingDistribution:
        """Calculate overall training intensity distribution"""
        if not analyses:
            return TrainingDistribution(
                total_activities=0,
                total_minutes=0,
                zone1_minutes=0,
                zone2_minutes=0,
                zone3_minutes=0,
                zone1_percent=0,
                zone2_percent=0,
                zone3_percent=0,
                adherence_score=0,
                recommendations=["No training data available"]
            )
        
        total_zone1_minutes = sum(a.zone1_minutes for a in analyses)
        total_zone2_minutes = sum(a.zone2_minutes for a in analyses)
        total_zone3_minutes = sum(a.zone3_minutes for a in analyses)
        total_minutes = total_zone1_minutes + total_zone2_minutes + total_zone3_minutes
        
        if total_minutes == 0:
            zone1_percent = zone2_percent = zone3_percent = 0
        else:
            zone1_percent = total_zone1_minutes / total_minutes * 100
            zone2_percent = total_zone2_minutes / total_minutes * 100
            zone3_percent = total_zone3_minutes / total_minutes * 100
        
        # Calculate adherence score (0-100)
        zone1_deviation = abs(zone1_percent - self.target_zone1_percent)
        zone2_deviation = abs(zone2_percent - self.target_zone2_percent)
        zone3_deviation = abs(zone3_percent - self.target_zone3_percent)
        
        # Weighted scoring (Zone 1 is most important)
        total_deviation = (zone1_deviation * 0.5) + (zone2_deviation * 0.25) + (zone3_deviation * 0.25)
        adherence_score = max(0, 100 - total_deviation)
        
        # Generate recommendations
        recommendations = []
        if zone1_percent < 75:
            recommendations.append("Increase low-intensity training volume (Zone 1)")
        if zone2_percent > 20:
            recommendations.append("Reduce moderate-intensity training (Zone 2)")
        if zone3_percent < 5:
            recommendations.append("Add more high-intensity intervals (Zone 3)")
        if zone3_percent > 15:
            recommendations.append("Reduce high-intensity training volume (Zone 3)")
        
        if adherence_score >= 80:
            recommendations.append("Excellent adherence to polarized training approach!")
        elif adherence_score >= 60:
            recommendations.append("Good training distribution with room for improvement")
        else:
            recommendations.append("Consider restructuring training to follow polarized approach")
        
        return TrainingDistribution(
            total_activities=len(analyses),
            total_minutes=int(total_minutes),
            zone1_minutes=int(total_zone1_minutes),
            zone2_minutes=int(total_zone2_minutes),
            zone3_minutes=int(total_zone3_minutes),
            zone1_percent=zone1_percent,
            zone2_percent=zone2_percent,
            zone3_percent=zone3_percent,
            adherence_score=adherence_score,
            recommendations=recommendations
        )
    
    def generate_report(self, distribution: TrainingDistribution, analyses: List[ActivityAnalysis]) -> str:
        """Generate a detailed training analysis report"""
        report = []
        report.append("=" * 60)
        report.append("POLARIZED TRAINING ANALYSIS REPORT")
        report.append("=" * 60)
        
        # Configuration
        report.append(f"\nConfiguration:")
        report.append(f"  Max Heart Rate: {self.max_hr} bpm")
        report.append(f"  FTP: {self.ftp} watts")
        report.append(f"  Zone 1 (Low): ≤{self.hr_zones.zone1_max} bpm / ≤{self.power_zones.zone1_max}W")
        report.append(f"  Zone 2 (Threshold): {self.hr_zones.zone1_max+1}-{self.hr_zones.zone2_max} bpm / {self.power_zones.zone1_max+1}-{self.power_zones.zone2_max}W")
        report.append(f"  Zone 3 (High): ≥{self.hr_zones.zone3_min+1} bpm / ≥{self.power_zones.zone3_min+1}W")
        
        # Overall Distribution
        report.append(f"\nTraining Distribution ({distribution.total_activities} activities, {distribution.total_minutes} minutes):")
        report.append(f"  Zone 1: {distribution.zone1_minutes} min ({distribution.zone1_percent:.1f}%) [Target: {self.target_zone1_percent}%]")
        report.append(f"  Zone 2: {distribution.zone2_minutes} min ({distribution.zone2_percent:.1f}%) [Target: {self.target_zone2_percent}%]")
        report.append(f"  Zone 3: {distribution.zone3_minutes} min ({distribution.zone3_percent:.1f}%) [Target: {self.target_zone3_percent}%]")
        
        # Adherence Score
        report.append(f"\nAdherence Score: {distribution.adherence_score:.1f}/100")
        
        # Recommendations
        report.append(f"\nRecommendations:")
        for rec in distribution.recommendations:
            report.append(f"  • {rec}")
        
        # Recent Activities
        report.append(f"\nRecent Activities:")
        for analysis in analyses[-10:]:  # Show last 10 activities
            report.append(f"  {analysis.name} ({analysis.date[:10]})")
            report.append(f"    Duration: {analysis.duration_minutes} min")
            report.append(f"    Zones: Z1={analysis.zone1_percent:.0f}% Z2={analysis.zone2_percent:.0f}% Z3={analysis.zone3_percent:.0f}%")
            if analysis.average_hr:
                report.append(f"    Avg HR: {analysis.average_hr} bpm")
            if analysis.average_power:
                report.append(f"    Avg Power: {analysis.average_power}W")
        
        return "\n".join(report)
    
    def _filter_activities_for_recommendations(self, analyses: List[ActivityAnalysis], 
                                             days: int = 14) -> List[ActivityAnalysis]:
        """Filter activities to recent period for recommendation analysis (research-based 14-day window)"""
        if not analyses:
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered = []
        
        for analysis in analyses:
            try:
                # Handle both ISO format with and without timezone
                activity_date_str = analysis.date.replace('Z', '+00:00') if analysis.date.endswith('Z') else analysis.date
                activity_date = datetime.fromisoformat(activity_date_str).replace(tzinfo=None)
                
                if activity_date >= cutoff_date:
                    filtered.append(analysis)
            except (ValueError, AttributeError):
                # Skip activities with invalid dates
                continue
        
        return filtered
    
    def get_workout_recommendations(self, all_analyses: List[ActivityAnalysis],
                                  target_weekly_hours: float = 8.0) -> List[WorkoutRecommendation]:
        """Generate workout recommendations based on research-backed 14-day analysis window"""
        recommendations = []
        
        # Filter to last 14 days for recommendations (research-based window)
        recent_analyses = self._filter_activities_for_recommendations(all_analyses, days=14)
        
        if not recent_analyses:
            # If no recent activities, provide general guidance
            recommendations.append(WorkoutRecommendation(
                workout_type=WorkoutType.EASY_AEROBIC,
                primary_zone=1,
                duration_minutes=60,
                description="Easy aerobic base workout",
                structure="60 minutes easy pace in Zone 1 to restart training",
                reasoning="No recent training data found. Start with easy aerobic base work",
                priority="high"
            ))
            return recommendations
        
        # Calculate distribution for recent 14-day period
        recent_distribution = self.calculate_training_distribution(recent_analyses)
        
        # Calculate deviations from target based on recent training
        zone1_deviation = recent_distribution.zone1_percent - self.target_zone1_percent
        zone2_deviation = recent_distribution.zone2_percent - self.target_zone2_percent 
        zone3_deviation = recent_distribution.zone3_percent - self.target_zone3_percent
        
        # Calculate absolute time considerations
        total_training_minutes = recent_distribution.total_minutes
        weekly_volume = total_training_minutes / 2  # 14 days = 2 weeks
        zone3_minutes = recent_distribution.zone3_minutes
        zone1_minutes = recent_distribution.zone1_minutes
        
        # Minimum thresholds based on research (per week)
        min_zone3_per_week = 30  # Minimum 30 minutes/week of Zone 3 for fitness maintenance
        min_total_volume_per_week = 180  # Minimum 3 hours/week for meaningful training
        
        # Analyze recent workout pattern
        last_workout_zones = self._analyze_recent_pattern(recent_analyses)
        days_since_last_intensity = self._days_since_last_intensity(recent_analyses)
        
        # Primary recommendation based on both percentages AND absolute time considerations
        
        # Check absolute volume first - insufficient total training
        if weekly_volume < min_total_volume_per_week:
            recommendations.append(self._recommend_volume_increase(weekly_volume, min_total_volume_per_week))
        
        # Check Zone 3 absolute time - insufficient high intensity
        elif (zone3_minutes / 2) < min_zone3_per_week and days_since_last_intensity > 4:
            recommendations.append(self._recommend_intensity_workout_volume(zone3_minutes / 2, days_since_last_intensity))
        
        # Check Zone 1 percentage deviation - need more aerobic base
        elif zone1_deviation < -10 or (zone1_minutes < total_training_minutes * 0.7):
            recommendations.append(self._recommend_aerobic_workout(zone1_deviation, target_weekly_hours, zone1_minutes))
        
        # Check Zone 2 excess - too much threshold work
        elif zone2_deviation > 5:
            recommendations.append(self._recommend_polarize_workout())
        
        # Check Zone 3 percentage deviation - need intensity but have minimum volume
        elif zone3_deviation < -3 and days_since_last_intensity > 3:
            recommendations.append(self._recommend_intensity_workout(days_since_last_intensity))
        
        # Balanced approach - maintain good distribution
        else:
            recommendations.append(self._recommend_balanced_workout(recent_distribution, last_workout_zones))
        
        # Secondary recommendations
        recommendations.extend(self._get_secondary_recommendations(recent_distribution, recent_analyses))
        
        return recommendations[:3]  # Return top 3 recommendations
    
    def _analyze_recent_pattern(self, recent_analyses: List[ActivityAnalysis]) -> Dict[str, int]:
        """Analyze pattern of recent workouts"""
        if not recent_analyses:
            return {"zone1": 0, "zone2": 0, "zone3": 0}
        
        # Look at last 3 workouts
        last_3 = recent_analyses[-3:]
        pattern = {"zone1": 0, "zone2": 0, "zone3": 0}
        
        for analysis in last_3:
            dominant_zone = max(
                [(1, analysis.zone1_percent), 
                 (2, analysis.zone2_percent), 
                 (3, analysis.zone3_percent)],
                key=lambda x: x[1]
            )[0]
            pattern[f"zone{dominant_zone}"] += 1
        
        return pattern
    
    def _days_since_last_intensity(self, recent_analyses: List[ActivityAnalysis]) -> int:
        """Calculate days since last high-intensity workout"""
        if not recent_analyses:
            return 7
        
        for i, analysis in enumerate(reversed(recent_analyses)):
            if analysis.zone3_percent > 15:  # Significant Zone 3 time
                return i
        
        return 7  # Default if no recent intensity found
    
    def _recommend_volume_increase(self, current_weekly_volume: float, min_weekly_volume: float) -> WorkoutRecommendation:
        """Recommend increasing overall training volume"""
        volume_deficit = min_weekly_volume - current_weekly_volume
        
        return WorkoutRecommendation(
            workout_type=WorkoutType.EASY_AEROBIC,
            primary_zone=1,
            duration_minutes=int(volume_deficit * 0.6),  # 60% of deficit in one workout
            description="Volume building aerobic workout",
            structure=f"{int(volume_deficit * 0.6)} minutes easy pace in Zone 1 to build training volume",
            reasoning=f"Your weekly training volume ({current_weekly_volume:.0f}min) is below minimum recommended ({min_weekly_volume}min)",
            priority="high"
        )
    
    def _recommend_intensity_workout_volume(self, current_zone3_per_week: float, days_since_intensity: int) -> WorkoutRecommendation:
        """Recommend intensity workout based on insufficient Zone 3 time"""
        return WorkoutRecommendation(
            workout_type=WorkoutType.INTERVALS,
            primary_zone=3,
            duration_minutes=75,
            description="High-intensity interval session",
            structure="15min warmup + 4x5min @ Zone 3 (3min recovery) + 15min cooldown",
            reasoning=f"You're only getting {current_zone3_per_week:.0f}min/week of Zone 3 (need ≥30min) and it's been {days_since_intensity} days",
            priority="high"
        )
    
    def _recommend_aerobic_workout(self, zone1_deviation: float, target_weekly_hours: float, zone1_minutes: float = None) -> WorkoutRecommendation:
        """Recommend aerobic base workout"""
        severity = abs(zone1_deviation)
        
        if severity > 20:
            duration = int(target_weekly_hours * 60 * 0.4)  # 40% of weekly volume
            workout_type = WorkoutType.LONG_AEROBIC
            description = "Long aerobic base ride/run"
            structure = f"{duration} minutes steady in Zone 1 (≤{self.hr_zones.zone1_max} bpm)"
            priority = "high"
        else:
            duration = int(target_weekly_hours * 60 * 0.25)  # 25% of weekly volume
            workout_type = WorkoutType.EASY_AEROBIC
            description = "Easy aerobic workout"
            structure = f"{duration} minutes easy pace in Zone 1"
            priority = "medium"
        
        return WorkoutRecommendation(
            workout_type=workout_type,
            primary_zone=1,
            duration_minutes=duration,
            description=description,
            structure=structure,
            reasoning=f"You need {abs(zone1_deviation):.1f}% more Zone 1 training to reach the 80% target",
            priority=priority
        )
    
    def _recommend_intensity_workout(self, days_since_intensity: int) -> WorkoutRecommendation:
        """Recommend high-intensity workout"""
        if days_since_intensity > 5:
            return WorkoutRecommendation(
                workout_type=WorkoutType.INTERVALS,
                primary_zone=3,
                duration_minutes=75,
                description="High-intensity interval session",
                structure="15min warmup + 5x4min @ Zone 3 (3min recovery) + 15min cooldown",
                reasoning=f"It's been {days_since_intensity} days since your last high-intensity session",
                priority="high"
            )
        else:
            return WorkoutRecommendation(
                workout_type=WorkoutType.THRESHOLD,
                primary_zone=2,
                duration_minutes=60,
                description="Threshold workout",
                structure="15min warmup + 3x8min @ Zone 2 (3min recovery) + 10min cooldown",
                reasoning="Maintain fitness with moderate threshold work",
                priority="medium"
            )
    
    def _recommend_polarize_workout(self) -> WorkoutRecommendation:
        """Recommend workout to reduce Zone 2 time"""
        return WorkoutRecommendation(
            workout_type=WorkoutType.EASY_AEROBIC,
            primary_zone=1,
            duration_minutes=90,
            description="Strict aerobic workout",
            structure=f"90 minutes strictly below {self.hr_zones.zone1_max} bpm - avoid the 'gray zone'",
            reasoning="You have too much Zone 2 training. Focus on pure aerobic base work",
            priority="high"
        )
    
    def _recommend_balanced_workout(self, distribution: TrainingDistribution, 
                                   last_workout_zones: Dict[str, int]) -> WorkoutRecommendation:
        """Recommend workout for balanced training"""
        # If last workout was intense, recommend easy
        if last_workout_zones.get("zone3", 0) > 0:
            return WorkoutRecommendation(
                workout_type=WorkoutType.EASY_AEROBIC,
                primary_zone=1,
                duration_minutes=60,
                description="Recovery/easy aerobic workout",
                structure="60 minutes easy pace in Zone 1 for active recovery",
                reasoning="Active recovery after recent intensity work",
                priority="medium"
            )
        
        # Otherwise recommend based on weekly pattern
        return WorkoutRecommendation(
            workout_type=WorkoutType.LONG_AEROBIC,
            primary_zone=1,
            duration_minutes=120,
            description="Aerobic base building workout",
            structure="2 hours steady aerobic pace - focus on efficiency and endurance",
            reasoning="Your training is well-balanced. Continue building aerobic base",
            priority="medium"
        )
    
    def _get_secondary_recommendations(self, distribution: TrainingDistribution,
                                     recent_analyses: List[ActivityAnalysis]) -> List[WorkoutRecommendation]:
        """Get additional workout recommendations"""
        secondary = []
        
        # Always suggest recovery if needed
        if len(recent_analyses) >= 3:
            recent_intensity = sum(1 for a in recent_analyses[-3:] if a.zone3_percent > 10)
            if recent_intensity >= 2:
                secondary.append(WorkoutRecommendation(
                    workout_type=WorkoutType.RECOVERY,
                    primary_zone=1,
                    duration_minutes=45,
                    description="Active recovery session",
                    structure="45 minutes very easy pace with mobility work",
                    reasoning="You've had multiple intense sessions recently",
                    priority="low"
                ))
        
        # Suggest technique work
        if distribution.zone2_percent < 15:  # If not overdoing Zone 2
            secondary.append(WorkoutRecommendation(
                workout_type=WorkoutType.TEMPO,
                primary_zone=2,
                duration_minutes=45,
                description="Tempo/technique workout",
                structure="10min warmup + 20min @ tempo pace (Zone 2) + 15min cooldown",
                reasoning="Optional tempo work to maintain neuromuscular fitness",
                priority="low"
            ))
        
        return secondary
