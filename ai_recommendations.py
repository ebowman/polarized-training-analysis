#!/usr/bin/env python
"""
AI-Powered Workout Recommendations

Integrates with OpenAI's API to provide personalized workout recommendations
based on polarized training principles, user preferences, and recent training data.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import openai
from dotenv import load_dotenv

load_dotenv()

# Training approach constants
POLARIZED_TARGETS = {'zone1': 80, 'zone2': 10, 'zone3': 10}
PYRAMIDAL_TARGETS = {'zone1': 70, 'zone2': 20, 'zone3': 10}
LOW_VOLUME_THRESHOLD = 4  # hours per week
PYRAMIDAL_VOLUME_THRESHOLD = 6  # hours per week
ANALYSIS_WINDOW_DAYS = 14

@dataclass
class AIWorkoutRecommendation:
    """AI-generated workout recommendation"""
    workout_type: str
    duration_minutes: int
    description: str
    structure: str
    reasoning: str
    equipment: str
    intensity_zones: List[int]
    priority: str
    generated_at: str

@dataclass
class TrainingAnalysis:
    """Results of training data analysis"""
    total_minutes: float
    weekly_hours: float
    zone1_percent: float
    zone2_percent: float
    zone3_percent: float
    adherence_score: float
    training_approach: str
    recent_activities: List[Dict]
    total_activities: int

@dataclass
class SchedulingContext:
    """Current scheduling context for workout recommendations"""
    day_of_week: str
    current_date: str
    already_worked_out_today: bool
    today_workouts: List[str]

class TrainingDataAnalyzer:
    """Handles training data calculations and analysis"""
    
    def __init__(self):
        self.targets = {
            'polarized': POLARIZED_TARGETS,
            'pyramidal': PYRAMIDAL_TARGETS
        }
    
    def filter_recent_activities(self, activities: List[Dict], days: int = ANALYSIS_WINDOW_DAYS) -> List[Dict]:
        """Filter activities to recent time window"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_activities = []
        
        for activity in activities:
            if 'date' not in activity:
                continue
                
            try:
                activity_date = datetime.fromisoformat(activity['date'].replace('Z', '+00:00'))
                # Compare dates without timezone info to avoid offset-naive/aware issues
                if activity_date.replace(tzinfo=None) >= cutoff_date:
                    recent_activities.append(activity)
            except (ValueError, TypeError):
                # If date parsing fails, include the activity to be safe
                recent_activities.append(activity)
        
        return recent_activities
    
    def calculate_zone_distribution(self, activities: List[Dict]) -> Tuple[float, float, float, float]:
        """Calculate zone percentages and total minutes from activities"""
        total_zone1_minutes = 0
        total_zone2_minutes = 0
        total_zone3_minutes = 0
        total_minutes = 0
        
        for activity in activities:
            activity_minutes = activity.get('duration_minutes', 0)
            total_zone1_minutes += activity_minutes * (activity.get('zone1_percent', 0) / 100)
            total_zone2_minutes += activity_minutes * (activity.get('zone2_percent', 0) / 100)
            total_zone3_minutes += activity_minutes * (activity.get('zone3_percent', 0) / 100)
            total_minutes += activity_minutes
        
        if total_minutes == 0:
            return 0, 0, 0, 0
            
        zone1_percent = (total_zone1_minutes / total_minutes * 100)
        zone2_percent = (total_zone2_minutes / total_minutes * 100)
        zone3_percent = (total_zone3_minutes / total_minutes * 100)
        
        return zone1_percent, zone2_percent, zone3_percent, total_minutes
    
    def calculate_adherence_score(self, zone1_percent: float, zone2_percent: float, 
                                zone3_percent: float, training_approach: str) -> float:
        """Calculate adherence score based on training approach targets"""
        # For low-volume training, use a more flexible approach
        if training_approach == "low-volume":
            # Low volume doesn't have strict targets, so give a moderate score
            # based on having some variety in training
            if zone1_percent > 50 and zone3_percent < 30:
                return 75.0  # Reasonable distribution for low volume
            else:
                return 50.0  # Could use improvement
        
        targets = self.targets[training_approach]
        
        zone1_deviation = abs(zone1_percent - targets['zone1'])
        zone2_deviation = abs(zone2_percent - targets['zone2'])
        zone3_deviation = abs(zone3_percent - targets['zone3'])
        
        total_deviation = (zone1_deviation * 0.5) + (zone2_deviation * 0.25) + (zone3_deviation * 0.25)
        adherence_score = max(0, 100 - total_deviation)
        
        return adherence_score
    
    def determine_training_approach(self, weekly_hours: float) -> str:
        """Determine optimal training approach based on weekly volume"""
        if weekly_hours < LOW_VOLUME_THRESHOLD:
            return "low-volume"
        elif weekly_hours < PYRAMIDAL_VOLUME_THRESHOLD:
            return "pyramidal"
        else:
            return "polarized"
    
    def calculate_recovery_metrics(self, activities: List[Dict]) -> Dict:
        """Calculate recovery-related metrics for overtraining prevention"""
        now = datetime.now()
        
        # Initialize metrics
        metrics = {
            'consecutive_training_days': 0,
            'zone3_last_3_days': 0,
            'total_minutes_last_3_days': 0,
            'trained_today': False,
            'today_minutes': 0,
            'last_rest_day': None,
            'weekly_volume_change': 0,
            'tomorrow_volume_after_rolloff': 0
        }
        
        # Sort activities by date (newest first)
        sorted_activities = sorted(activities, 
                                 key=lambda x: datetime.fromisoformat(x['date'].replace('Z', '+00:00')).replace(tzinfo=None), 
                                 reverse=True)
        
        # Check if trained today
        today_str = now.strftime('%Y-%m-%d')
        for activity in sorted_activities:
            if today_str in activity['date']:
                metrics['trained_today'] = True
                metrics['today_minutes'] += activity.get('duration_minutes', 0)
        
        # Count consecutive training days
        current_date = now.date()
        consecutive_days = 0
        
        for i in range(14):  # Look back up to 2 weeks
            day_to_check = current_date - timedelta(days=i)
            day_str = day_to_check.strftime('%Y-%m-%d')
            
            # Check if any activity on this day
            day_has_activity = any(day_str in act['date'] for act in sorted_activities)
            
            if day_has_activity:
                consecutive_days += 1
            else:
                metrics['last_rest_day'] = day_str
                break
        
        metrics['consecutive_training_days'] = consecutive_days
        
        # Calculate Zone 3 accumulation in last 3 days
        three_days_ago = now - timedelta(days=3)
        for activity in sorted_activities:
            activity_date = datetime.fromisoformat(activity['date'].replace('Z', '+00:00'))
            # Convert to naive datetime for comparison
            activity_date_naive = activity_date.replace(tzinfo=None)
            if activity_date_naive >= three_days_ago:
                duration = activity.get('duration_minutes', 0)
                zone3_percent = activity.get('zone3_percent', 0)
                metrics['total_minutes_last_3_days'] += duration
                metrics['zone3_last_3_days'] += duration * (zone3_percent / 100)
        
        # Calculate Zone 3 percentage for last 3 days
        if metrics['total_minutes_last_3_days'] > 0:
            metrics['zone3_percent_last_3_days'] = (metrics['zone3_last_3_days'] / metrics['total_minutes_last_3_days']) * 100
        else:
            metrics['zone3_percent_last_3_days'] = 0
        
        # Calculate what volume will be tomorrow (after today rolls off the 7-day window)
        tomorrow = now + timedelta(days=1)
        seven_days_from_tomorrow = tomorrow - timedelta(days=7)
        
        tomorrow_volume = 0
        for activity in sorted_activities:
            activity_date = datetime.fromisoformat(activity['date'].replace('Z', '+00:00'))
            # Convert to naive datetime for comparison
            activity_date_naive = activity_date.replace(tzinfo=None)
            # Include activities from 6 days before tomorrow through tomorrow (which won't have any)
            if seven_days_from_tomorrow <= activity_date_naive < tomorrow:
                tomorrow_volume += activity.get('duration_minutes', 0)
        
        metrics['tomorrow_volume_after_rolloff'] = tomorrow_volume
        
        # Calculate weekly volume change
        this_week_volume = sum(act.get('duration_minutes', 0) 
                              for act in sorted_activities 
                              if datetime.fromisoformat(act['date'].replace('Z', '+00:00')).replace(tzinfo=None) >= now - timedelta(days=7))
        
        last_week_volume = sum(act.get('duration_minutes', 0) 
                              for act in sorted_activities 
                              if now - timedelta(days=14) <= datetime.fromisoformat(act['date'].replace('Z', '+00:00')).replace(tzinfo=None) < now - timedelta(days=7))
        
        metrics['this_week_volume'] = this_week_volume
        
        if last_week_volume > 0:
            metrics['weekly_volume_change'] = ((this_week_volume - last_week_volume) / last_week_volume) * 100
        else:
            metrics['weekly_volume_change'] = 0
            
        return metrics
    
    def analyze_training_data(self, training_data: Dict) -> TrainingAnalysis:
        """Complete analysis of training data"""
        activities = training_data.get('activities', [])
        recent_activities = self.filter_recent_activities(activities)
        
        zone1_percent, zone2_percent, zone3_percent, total_minutes = \
            self.calculate_zone_distribution(recent_activities)
        
        weekly_hours = total_minutes / 60
        training_approach = self.determine_training_approach(weekly_hours)
        
        adherence_score = self.calculate_adherence_score(
            zone1_percent, zone2_percent, zone3_percent, training_approach
        )
        
        return TrainingAnalysis(
            total_minutes=total_minutes,
            weekly_hours=weekly_hours,
            zone1_percent=zone1_percent,
            zone2_percent=zone2_percent,
            zone3_percent=zone3_percent,
            adherence_score=adherence_score,
            training_approach=training_approach,
            recent_activities=recent_activities,
            total_activities=len(recent_activities)
        )

class SchedulingContextProvider:
    """Manages day-of-week and scheduling context"""
    
    def get_current_context(self, recent_activities: List[Dict]) -> SchedulingContext:
        """Get current scheduling context"""
        today = datetime.now()
        day_of_week = today.strftime("%A")
        current_date = today.strftime("%Y-%m-%d")
        
        # Check if user already worked out today
        today_workouts = [
            a for a in recent_activities 
            if a.get('date', '')[:10] == current_date
        ]
        already_worked_out_today = len(today_workouts) > 0
        today_workout_names = [w.get('name', 'Unknown') for w in today_workouts]
        
        return SchedulingContext(
            day_of_week=day_of_week,
            current_date=current_date,
            already_worked_out_today=already_worked_out_today,
            today_workouts=today_workout_names
        )

class PromptBuilder:
    """Constructs AI prompts from training analysis components"""
    
    def __init__(self):
        self.analyzer = TrainingDataAnalyzer()
        self.scheduling_provider = SchedulingContextProvider()
    
    def load_user_preferences(self) -> str:
        """Load user workout preferences from markdown file with fallback"""
        preference_files = [
            'workout_preferences_personal.md',  # Personal file (not in git)
            'workout_preferences.md'            # Default file (in git)
        ]
        
        for preference_file in preference_files:
            try:
                with open(preference_file, 'r') as f:
                    content = f.read()
                    print(f"📝 Using preferences from: {preference_file}")
                    return self._process_hr_ranges(content)
            except FileNotFoundError:
                continue
        
        return "No user preferences file found. Using general recommendations."
    
    def _process_hr_ranges(self, content: str) -> str:
        """Replace static HR ranges with dynamic ones based on current max HR"""
        max_hr = int(os.getenv("MAX_HEART_RATE", "171"))
        
        # Calculate and substitute dynamic HR ranges
        hr2_range = f"{int(max_hr * 0.70)}-{int(max_hr * 0.82)} bpm"
        hr34_range = f"{int(max_hr * 0.82)}-{int(max_hr * 0.93)} bpm"
        hr5_range = f"{int(max_hr * 0.93)}+ bpm"
        
        # Replace any hardcoded ranges with dynamic ones
        content = content.replace("120-140 bpm", hr2_range)
        content = content.replace("140-159 bpm", hr34_range)
        content = content.replace("159+ bpm", hr5_range)
        content = content.replace("171 bpm", f"{max_hr} bpm")
        
        return content
    
    def load_nih_research_summary(self) -> str:
        """Load NIH research summary for context"""
        try:
            with open('nih_polarized_training_summary.md', 'r') as f:
                return f.read()
        except FileNotFoundError:
            return "NIH research summary not available."
    
    def create_training_context(self, analysis: TrainingAnalysis, 
                              scheduling: SchedulingContext, training_data: Dict, 
                              recovery_metrics: Dict = None) -> str:
        """Create comprehensive training context for AI"""
        context = []
        
        # Current training analysis
        context.append(f"## Current Training Analysis (Last {ANALYSIS_WINDOW_DAYS} Days)")
        context.append(f"- Total Activities: {analysis.total_activities}")
        context.append(f"- Total Training Time: {analysis.total_minutes:.0f} minutes")
        context.append(f"- Today: {scheduling.day_of_week} ({scheduling.current_date})")
        context.append(f"- Already worked out today: {'Yes' if scheduling.already_worked_out_today else 'No'}")
        
        if scheduling.already_worked_out_today:
            context.append(f"- Today's workouts: {', '.join(scheduling.today_workouts)}")
        
        # Debug logging
        old_dist = training_data.get('distribution', {})
        print(f"🐛 AI Debug - OLD distribution data: Zone1={old_dist.get('zone1_percent', 0):.1f}% Zone2={old_dist.get('zone2_percent', 0):.1f}% Zone3={old_dist.get('zone3_percent', 0):.1f}%")
        print(f"🐛 AI Debug - NEW calculated data: Zone1={analysis.zone1_percent:.1f}% Zone2={analysis.zone2_percent:.1f}% Zone3={analysis.zone3_percent:.1f}%")
        print(f"🐛 AI using {analysis.total_activities} activities from last {ANALYSIS_WINDOW_DAYS} days")
        
        # Debug: Show total minutes calculation
        print(f"🐛 AI Debug - Total minutes: {analysis.total_minutes:.1f}")
        print(f"🐛 AI Debug - Zone minutes: Z1={analysis.total_minutes * analysis.zone1_percent / 100:.1f}, Z2={analysis.total_minutes * analysis.zone2_percent / 100:.1f}, Z3={analysis.total_minutes * analysis.zone3_percent / 100:.1f}")
        
        # Debug: Show recent activity dates to verify filtering
        recent_dates = [a.get('date', '')[:10] for a in analysis.recent_activities[:5]]
        print(f"🐛 AI Debug - First 5 activity dates (most recent): {recent_dates}")
        oldest_dates = [a.get('date', '')[:10] for a in analysis.recent_activities[-5:]]
        print(f"🐛 AI Debug - Last 5 activity dates (oldest in window): {oldest_dates}")
        
        # Debug: Show date range of ALL activities being analyzed
        all_dates = [a.get('date', '')[:10] for a in analysis.recent_activities if a.get('date')]
        if all_dates:
            earliest = min(all_dates)
            latest = max(all_dates)
            print(f"🐛 AI Debug - Date range of {len(analysis.recent_activities)} activities: {earliest} to {latest}")
            print(f"🐛 AI Debug - Today is: {datetime.now().strftime('%Y-%m-%d')}")
            
            # Check if we have any activities from the last 7 days
            last_week = datetime.now() - timedelta(days=7)
            recent_week_activities = []
            for a in analysis.recent_activities:
                if a.get('date'):
                    try:
                        activity_date = datetime.fromisoformat(a['date'].replace('Z', '+00:00'))
                        # Compare dates without timezone info to avoid offset-naive/aware issues
                        if activity_date.replace(tzinfo=None) >= last_week:
                            recent_week_activities.append(a)
                    except (ValueError, TypeError):
                        continue
            print(f"🐛 AI Debug - Activities from last 7 days: {len(recent_week_activities)}")
        else:
            print(f"🐛 AI Debug - No activities with dates found!")
        
        # Zone analysis with status indicators
        context.append(f"- Zone 1 (Low): {analysis.zone1_percent:.1f}% [Target: 80%] {'❌ BELOW TARGET' if analysis.zone1_percent < 80 else '✅ ADEQUATE'}")
        context.append(f"- Zone 2 (Threshold): {analysis.zone2_percent:.1f}% [Target: 10%] {'❌ ABOVE TARGET' if analysis.zone2_percent > 10 else '✅ ADEQUATE'}")
        context.append(f"- Zone 3 (High): {analysis.zone3_percent:.1f}% [Target: 10%] {'❌ ABOVE TARGET' if analysis.zone3_percent > 10 else '✅ ADEQUATE'}")
        context.append(f"- Adherence Score: {analysis.adherence_score:.1f}/100")
        
        # Volume and approach guidance
        context.append(f"- Weekly Volume: {analysis.weekly_hours:.1f} hours")
        context.append(f"- Training Approach: {analysis.training_approach.upper()} (based on {analysis.weekly_hours:.1f} hrs/week)")
        
        # Volume-based guidance
        if analysis.weekly_hours < LOW_VOLUME_THRESHOLD:
            context.append(f"📊 VOLUME GUIDANCE: <{LOW_VOLUME_THRESHOLD} hours/week - Consider basic fitness approach with mixed intensities")
        elif analysis.weekly_hours < PYRAMIDAL_VOLUME_THRESHOLD:
            context.append(f"📊 VOLUME GUIDANCE: {analysis.weekly_hours:.1f} hours/week - Pyramidal approach may be better (70% Z1, 20% Z2, 10% Z3)")
        else:
            context.append(f"📊 VOLUME GUIDANCE: {analysis.weekly_hours:.1f} hours/week - Sufficient volume for polarized training (80% Z1, 10% Z2, 10% Z3)")
        
        # Training guidance based on current state
        if analysis.zone3_percent >= 10:
            context.append(f"⚠️ CRITICAL: Zone 3 is ALREADY at {analysis.zone3_percent:.1f}% (target is 10%). ABSOLUTELY NO high-intensity workouts!")
            context.append(f"🚫 ZONE 3 PROHIBITION: Current Z3 = {analysis.zone3_percent:.1f}% ≥ 10% target. Focus ONLY on Zone 1 aerobic base.")
        elif analysis.zone3_percent >= 8:
            context.append(f"⚠️ CAUTION: Zone 3 is at {analysis.zone3_percent:.1f}% (close to 10% target). Avoid high-intensity unless absolutely necessary.")
        
        if analysis.zone1_percent < 80 and analysis.training_approach == "polarized":
            context.append(f"🎯 PRIORITY: Increase Zone 1 from {analysis.zone1_percent:.1f}% to 80%. Focus on aerobic base building.")
        elif analysis.zone1_percent < 70 and analysis.training_approach == "pyramidal":
            context.append(f"🎯 PRIORITY: Increase Zone 1 from {analysis.zone1_percent:.1f}% to 70% (pyramidal approach for your volume).")
        
        # Add recovery metrics if available
        if recovery_metrics:
            context.append(f"\\n## Recovery & Training Load Assessment")
            context.append(f"- Consecutive training days: {recovery_metrics['consecutive_training_days']}")
            context.append(f"- Zone 3 in last 3 days: {recovery_metrics['zone3_percent_last_3_days']:.1f}%")
            context.append(f"- Weekly volume change: {recovery_metrics['weekly_volume_change']:+.1f}%")
            context.append(f"- Tomorrow's projected volume: {recovery_metrics['tomorrow_volume_after_rolloff']} min")
            
            # Debug logging
            print(f"🐛 Recovery Metrics Debug:")
            print(f"  - Current week volume: {recovery_metrics.get('this_week_volume', 0)} min")
            print(f"  - Consecutive days: {recovery_metrics['consecutive_training_days']}")
            print(f"  - Zone 3 last 3 days: {recovery_metrics['zone3_percent_last_3_days']:.1f}%")
            print(f"  - Weekly volume change: {recovery_metrics['weekly_volume_change']:.1f}%")
            print(f"  - Tomorrow's volume: {recovery_metrics['tomorrow_volume_after_rolloff']} min")
            print(f"  - Trained today: {recovery_metrics['trained_today']}")
            print(f"  - Today's minutes: {recovery_metrics['today_minutes']}")
            
            # Recovery recommendations based on metrics
            if recovery_metrics['consecutive_training_days'] >= 5:
                context.append(f"⚠️ REST DAY RECOMMENDED: {recovery_metrics['consecutive_training_days']} consecutive training days")
            
            if recovery_metrics['zone3_percent_last_3_days'] > 15:
                context.append(f"⚠️ HIGH INTENSITY OVERLOAD: Zone 3 at {recovery_metrics['zone3_percent_last_3_days']:.1f}% in last 3 days")
            
            if recovery_metrics['weekly_volume_change'] > 30:
                context.append(f"⚠️ VOLUME SPIKE: {recovery_metrics['weekly_volume_change']:.1f}% increase from last week")
            
            if recovery_metrics['tomorrow_volume_after_rolloff'] > 360:
                context.append(f"📊 Tomorrow you'll still be at {recovery_metrics['tomorrow_volume_after_rolloff']} min (above 360 target)")
        
        # Recent activities
        recent_activities = analysis.recent_activities[:5]  # First 5 activities (most recent)
        if recent_activities:
            context.append(f"\\n## Recent Activities")
            for activity in recent_activities:
                context.append(f"- {activity.get('name', 'Unknown')} ({activity.get('date', '')[:10]})")
                context.append(f"  Duration: {activity.get('duration_minutes', 0)} min")
                context.append(f"  Zones: Z1={activity.get('zone1_percent', 0):.0f}% Z2={activity.get('zone2_percent', 0):.0f}% Z3={activity.get('zone3_percent', 0):.0f}%")
        
        # Current recommendations from rule-based system
        current_recs = training_data.get('workout_recommendations', [])
        if current_recs:
            context.append(f"\\n## Current Algorithm Recommendations")
            for i, rec in enumerate(current_recs[:3], 1):
                context.append(f"{i}. {rec.get('description', '')} ({rec.get('duration_minutes', 0)} min)")
                context.append(f"   Structure: {rec.get('structure', '')}")
                context.append(f"   Reasoning: {rec.get('reasoning', '')}")
        
        return "\\n".join(context)
    
    def build_prompt(self, training_data: Dict, num_recommendations: int = 3) -> str:
        """Build complete AI prompt from components"""
        # Analyze training data
        analysis = self.analyzer.analyze_training_data(training_data)
        scheduling = self.scheduling_provider.get_current_context(analysis.recent_activities)
        
        # Calculate recovery metrics
        recovery_metrics = self.analyzer.calculate_recovery_metrics(training_data.get('activities', []))
        
        # Load context components
        user_preferences = self.load_user_preferences()
        nih_research = self.load_nih_research_summary()
        training_context = self.create_training_context(analysis, scheduling, training_data, recovery_metrics)
        
        # Build complete prompt
        prompt = f"""
You are an expert endurance coach with deep knowledge of polarized training methodology. 
Based on the NIH research and the athlete's recent training data, provide personalized workout recommendations.

{nih_research}

## Zone System Guidelines
Use activity-specific zone terminology:

**For Cycling (Peloton/FTP-based):**
- Use "Power Zone X" terminology (e.g., "Power Zone 2", "Power Zone 4")
- Power Zone 1-3 (0-90% FTP) = Polarized Zone 1 (aerobic base)
- Power Zone 4 (90-105% FTP) = Polarized Zone 2 (threshold)
- Power Zone 5-6 (105%+ FTP) = Polarized Zone 3 (high intensity)
- Current FTP: {training_data.get('config', {}).get('ftp', 301)} watts

**For Rowing (HR-based):**
- Use "HR Zone X" terminology with actual BPM ranges
- HR Zone 1-2 ({int(training_data.get('config', {}).get('max_hr', 171) * 0.5)}-{int(training_data.get('config', {}).get('max_hr', 171) * 0.82)} bpm) = Polarized Zone 1 (aerobic base)
- HR Zone 3-4 ({int(training_data.get('config', {}).get('max_hr', 171) * 0.82)}-{int(training_data.get('config', {}).get('max_hr', 171) * 0.93)} bpm) = Polarized Zone 2 (threshold)
- HR Zone 5 ({int(training_data.get('config', {}).get('max_hr', 171) * 0.93)}+ bpm) = Polarized Zone 3 (high intensity)
- Current Max HR: {training_data.get('config', {}).get('max_hr', 171)} bpm

**For Strength Training:**
- Use RPE (Rate of Perceived Exertion) 1-10 scale
- Focus on functional strength for endurance athletes

## Athlete's Training Preferences & Goals
{user_preferences}

## Current Training Status
{training_context}

## Task
Generate {num_recommendations} specific, actionable workout recommendations appropriate for TODAY and the next few days. 
Consider the current day of the week and whether they've already trained today.

🚫 CRITICAL ZONE 3 CHECK: Current Zone 3 = {analysis.zone3_percent:.1f}%
- IF Zone 3 ≥ 10.0%: ABSOLUTELY NO HIGH-INTENSITY WORKOUTS (no Power Zone 5-6, no VO2-max, no intervals above threshold)
- CURRENT STATUS: {'ZONE 3 IS ABOVE TARGET - NO HIGH INTENSITY ALLOWED' if analysis.zone3_percent >= 10 else 'Zone 3 below target - high intensity appropriate if needed'}

🛑 REST DAY PRIORITY CHECK:
- Current rolling 7-day volume: {recovery_metrics.get('this_week_volume', 'unknown') if recovery_metrics else 'unknown'} minutes
- Tomorrow's projected volume: {recovery_metrics.get('tomorrow_volume_after_rolloff', 'unknown') if recovery_metrics else 'unknown'} minutes
- IF current volume > 360 min AND consecutive days ≥ 5: RECOMMEND REST DAY as first option
- IF current volume > 360 min AND Zone 1 > 85%: Consider short Zone 3 workout (15-20 min) OR rest day  
- IF tomorrow's volume will still be > 360 min: Strongly consider rest day
- REST DAY recommendation format: {{"workout_type": "Rest Day", "duration_minutes": 0, "description": "Complete rest to allow adaptation", "structure": "No training - focus on recovery, hydration, and sleep", "reasoning": "[explain why based on current metrics]", "equipment": "None", "intensity_zones": [], "priority": "high"}}

Each recommendation should be formatted as valid JSON with these fields:
- workout_type: (e.g., "Power Zone Endurance Ride", "HR Zone Steady State Row", "Functional Strength")
- duration_minutes: (integer)
- description: (brief, engaging description using correct zone terminology)
- structure: (detailed workout structure with specific power zones for cycling, HR zones for rowing)
- reasoning: (why this workout fits their current needs and goals)
- equipment: (e.g., "Peloton", "Concept2 RowERG", "Dumbbells", "Bodyweight")
- intensity_zones: (array of polarized zones used for analysis, e.g., [1], [2], [3], [1,3])
- priority: ("high", "medium", or "low")

Examples:
- Cycling: "Power Zone 2 endurance ride (65-75% FTP) for 90 minutes"
- Rowing: "HR Zone 2 steady state ({int(training_data.get('config', {}).get('max_hr', 171) * 0.70)}-{int(training_data.get('config', {}).get('max_hr', 171) * 0.82)} bpm) for 45 minutes"
- Strength: "Functional strength circuit at RPE 6-7 for 30 minutes"

Consider:
1. Their specific goals (FTP improvement, multi-modal training)
2. **VOLUME-BASED TRAINING APPROACH** (most important factor):
   - **<{LOW_VOLUME_THRESHOLD} hours/week**: Mixed approach, focus on general fitness
   - **{LOW_VOLUME_THRESHOLD}-{PYRAMIDAL_VOLUME_THRESHOLD} hours/week**: PYRAMIDAL approach (70% Z1, 20% Z2, 10% Z3) - More Zone 2 threshold work
   - **>{PYRAMIDAL_VOLUME_THRESHOLD} hours/week**: POLARIZED approach (80% Z1, 10% Z2, 10% Z3) - Minimal Zone 2
3. Current training distribution vs. volume-appropriate targets:
   - **Polarized (>{PYRAMIDAL_VOLUME_THRESHOLD} hrs/week)**: If Zone 1 < 80% OR Zone 3 > 10%, focus on Zone 1
   - **Pyramidal ({LOW_VOLUME_THRESHOLD}-{PYRAMIDAL_VOLUME_THRESHOLD} hrs/week)**: If Zone 1 < 70% OR Zone 2 < 20%, adjust accordingly
   - Only recommend Zone 3 if current Zone 3 is significantly below target
4. Equipment preferences (Peloton, RowERG, dumbbells)
5. Recovery needs based on recent training
6. Progressive overload principles
7. Variety to prevent boredom
8. Use correct zone terminology for each activity type

CRITICAL RULES - READ CAREFULLY:
- **Volume determines training approach**: Use pyramidal targets for <{PYRAMIDAL_VOLUME_THRESHOLD} hrs/week, polarized for >{PYRAMIDAL_VOLUME_THRESHOLD} hrs/week
- **🚫 ZONE 3 PROHIBITION**: If current Zone 3 ≥ 10%, DO NOT recommend ANY high-intensity workouts (Power Zone 5-6, VO2 max, HIIT, intervals above threshold)
- **ZONE 3 MATH CHECK**: If Zone 3 percentage is 10.0% or higher, the athlete has ENOUGH high-intensity. Focus on Zone 1 only.
- **Zone 2 threshold work**: More appropriate for pyramidal (limited volume) athletes
- **When Zone 3 is adequate**: Only recommend Zone 1 (aerobic base) and Zone 2 (threshold) workouts
- **🛑 RECOVERY RULES**:
  - **5+ consecutive training days**: MUST recommend rest day or very light recovery (max 30 min Zone 1)
  - **Zone 3 > 15% in last 3 days**: NO high-intensity work, focus on Zone 1 recovery
  - **Weekly volume increase > 30%**: Reduce intensity and volume to prevent overtraining
  - **Tomorrow's volume > 360 min**: If they'll still be above target tomorrow, recommend rest or very light activity
  - **Already trained today**: Be conservative with additional recommendations
- **DAY-OF-WEEK SCHEDULING**:
  - **Monday-Friday**: Recommend 30-75 minute workouts (work day constraints)
  - **Saturday-Sunday**: Longer sessions (90+ minutes) are appropriate for weekend
  - **Already worked out today**: Recommend recovery/easy day or suggest "rest day - try tomorrow"
  - **Monday/Tuesday**: Good for high-intensity if needed (fresh start of week)
  - **Wednesday/Thursday**: Mixed approach, consider mid-week recovery
  - **Friday**: Lean toward easier sessions (end of work week)
  - **Weekend**: Ideal for long Zone 1 aerobic base sessions

Return only a JSON array of workout recommendations, no other text.
"""
        
        return prompt

class AIRecommendationEngine:
    """AI-powered workout recommendation engine using OpenAI"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            raise ValueError("Please set your OpenAI API key in the .env file")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4o"
        self.fallback_model = "gpt-4o-mini"
        self.prompt_builder = PromptBuilder()
        
        # Default retry configuration
        self.max_retries = 3
    
    def generate_ai_recommendations(self, training_data: Dict, 
                                  num_recommendations: int = 3) -> List[AIWorkoutRecommendation]:
        """Generate AI-powered workout recommendations using the new architecture"""
        
        # Build prompt using the new PromptBuilder
        prompt = self.prompt_builder.build_prompt(training_data, num_recommendations)
        
        # Call OpenAI API with retry logic
        return self._call_openai_with_retry(prompt)
    
    def _call_openai_with_retry(self, prompt: str) -> List[AIWorkoutRecommendation]:
        """Call OpenAI API with retry logic and error handling"""
        
        for attempt in range(self.max_retries):
            try:
                # Use fallback model on the last attempt if o3 keeps failing
                current_model = self.fallback_model if attempt == self.max_retries - 1 else self.model
                print(f"🤖 Calling OpenAI {current_model} model (attempt {attempt + 1}/{self.max_retries})...")
                
                if attempt == 0:  # Only log prompt details on first attempt
                    print(f"📝 Prompt length: {len(prompt)} characters")
                    print(f"📋 Prompt preview (first 500 chars):\n{prompt[:500]}...")
                    print(f"📋 Prompt ending (last 200 chars):\n...{prompt[-200:]}")
                
                # Prepare API parameters based on model
                api_params = self._prepare_api_params(current_model, prompt)
                
                # Call OpenAI API
                response = self.client.chat.completions.create(**api_params)
                
                # Validate and parse response
                recommendations = self._parse_response(response)
                
                print(f"✅ Successfully generated {len(recommendations)} recommendations")
                return recommendations
                
            except json.JSONDecodeError as e:
                if attempt < self.max_retries - 1:
                    print(f"⚠️  JSON decode error, retrying: {e}")
                    continue
                else:
                    print(f"❌ JSON decode failed after all retries: {e}")
                    return self._create_fallback_recommendations(f"JSON decode error: {e}")
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"⚠️  Error on attempt {attempt + 1}, retrying: {e}")
                    continue
                else:
                    print(f"❌ All retry attempts failed: {e}")
                    return self._create_fallback_recommendations(f"All attempts failed: {e}")
        
        # If we get here, all retries failed
        return self._create_fallback_recommendations(f"All {self.max_retries} attempts failed")
    
    def _prepare_api_params(self, model: str, prompt: str) -> dict:
        """Prepare API parameters based on model type"""
        api_params = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if model == "o3":
            api_params["max_completion_tokens"] = 2000
        else:
            api_params["max_tokens"] = 2000
            api_params["temperature"] = 0.7
        
        return api_params
    
    def _parse_response(self, response) -> List[AIWorkoutRecommendation]:
        """Parse and validate OpenAI response"""
        print(f"✅ OpenAI response received")
        print(f"Response object type: {type(response)}")
        print(f"Response choices length: {len(response.choices) if response.choices else 0}")
        
        if not response.choices or not response.choices[0].message:
            raise ValueError("OpenAI returned no message content")
        
        recommendations_json = response.choices[0].message.content
        
        if recommendations_json is None:
            raise ValueError("OpenAI returned None for message content")
            
        recommendations_json = recommendations_json.strip()
        
        # Debug logging
        print(f"AI Response length: {len(recommendations_json)} characters")
        if len(recommendations_json) < 10:
            print(f"AI Response content: {repr(recommendations_json)}")
        elif len(recommendations_json) < 100:
            print(f"Short AI Response: {recommendations_json[:100]}...")
        
        # Clean up response (remove code blocks if present)
        recommendations_json = self._clean_json_response(recommendations_json)
        
        if not recommendations_json:
            raise ValueError("AI returned empty response after cleanup")
        
        # Parse JSON and convert to recommendation objects
        recommendations_data = json.loads(recommendations_json)
        return self._convert_to_recommendations(recommendations_data)
    
    def _clean_json_response(self, response: str) -> str:
        """Clean up JSON response by removing code blocks"""
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]
        return response.strip()
    
    def _convert_to_recommendations(self, recommendations_data: List[dict]) -> List[AIWorkoutRecommendation]:
        """Convert parsed JSON data to AIWorkoutRecommendation objects"""
        ai_recommendations = []
        
        for rec_data in recommendations_data:
            ai_rec = AIWorkoutRecommendation(
                workout_type=rec_data.get('workout_type', 'Unknown'),
                duration_minutes=rec_data.get('duration_minutes', 60),
                description=rec_data.get('description', ''),
                structure=rec_data.get('structure', ''),
                reasoning=rec_data.get('reasoning', ''),
                equipment=rec_data.get('equipment', 'General'),
                intensity_zones=rec_data.get('intensity_zones', [1]),
                priority=rec_data.get('priority', 'medium'),
                generated_at=datetime.now().isoformat()
            )
            ai_recommendations.append(ai_rec)
        
        return ai_recommendations
    
    def _create_fallback_recommendations(self, error_message: str) -> List[AIWorkoutRecommendation]:
        """Create fallback recommendations when AI fails"""
        return [AIWorkoutRecommendation(
            workout_type="Fallback Workout",
            duration_minutes=60,
            description="Easy aerobic workout",
            structure="60 minutes easy pace in Zone 1",
            reasoning=f"AI service unavailable: {error_message}",
            equipment="General",
            intensity_zones=[1],
            priority="medium",
            generated_at=datetime.now().isoformat()
        )]
    
    def save_recommendation_history(self, recommendations: List[AIWorkoutRecommendation], 
                                  filename: str = "cache/ai_recommendation_history.json"):
        """Save AI recommendations to history file"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "recommendations": [asdict(rec) for rec in recommendations]
        }
        
        # Load existing history
        history = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    history = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                history = []
        
        # Add new entry
        history.append(history_entry)
        
        # Keep only last 50 entries to prevent file from growing too large
        history = history[-50:]
        
        # Save updated history
        with open(filename, 'w') as f:
            json.dump(history, f, indent=2)
    
    def load_recommendation_history(self, filename: str = "cache/ai_recommendation_history.json") -> List[Dict]:
        """Load AI recommendation history"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

def main():
    """Test the AI recommendation engine"""
    engine = AIRecommendationEngine()
    
    # Sample training data for testing
    sample_data = {
        'distribution': {
            'total_activities': 10,
            'total_minutes': 600,
            'zone1_percent': 70.0,
            'zone2_percent': 20.0,
            'zone3_percent': 10.0,
            'adherence_score': 75.0
        },
        'activities': [
            {
                'name': 'Morning Ride',
                'date': '2025-01-01T08:00:00Z',
                'duration_minutes': 60,
                'zone1_percent': 80,
                'zone2_percent': 15,
                'zone3_percent': 5
            }
        ],
        'workout_recommendations': [
            {
                'description': 'Easy aerobic workout',
                'duration_minutes': 60,
                'structure': '60 minutes easy pace',
                'reasoning': 'Need more Zone 1 training'
            }
        ]
    }
    
    recommendations = engine.generate_ai_recommendations(sample_data)
    
    print("AI Workout Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"\\n{i}. {rec.workout_type} ({rec.duration_minutes} min)")
        print(f"   Equipment: {rec.equipment}")
        print(f"   Description: {rec.description}")
        print(f"   Structure: {rec.structure}")
        print(f"   Reasoning: {rec.reasoning}")
        print(f"   Priority: {rec.priority}")

if __name__ == "__main__":
    main()