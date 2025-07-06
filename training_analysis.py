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
