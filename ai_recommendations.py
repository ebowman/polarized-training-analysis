#!/usr/bin/env python
"""
AI-Powered Workout Recommendations

Integrates with OpenAI's API to provide personalized workout recommendations
based on polarized training principles, user preferences, and recent training data.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import openai
from dotenv import load_dotenv

load_dotenv()

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

class AIRecommendationEngine:
    """AI-powered workout recommendation engine using OpenAI"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            raise ValueError("Please set your OpenAI API key in the .env file")
        
        self.client = openai.OpenAI(
            api_key=api_key
        )
        # Use OpenAI's o3 model for advanced reasoning and analysis
        self.model = "o3"
        self.fallback_model = "gpt-4o"  # More reliable fallback
    
    def load_user_preferences(self) -> str:
        """Load user workout preferences from markdown file with fallback"""
        # Try personal preferences first (not in git)
        preference_files = [
            'workout_preferences_personal.md',  # Personal file (not in git)
            'workout_preferences.md'            # Default file (in git)
        ]
        
        content = None
        used_file = None
        
        for preference_file in preference_files:
            try:
                with open(preference_file, 'r') as f:
                    content = f.read()
                    used_file = preference_file
                    break
            except FileNotFoundError:
                continue
        
        if content is None:
            return "No user preferences file found. Using general recommendations."
        
        # Replace static HR ranges with dynamic ones based on current max HR
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
        
        # Add a note about which file was used (for debugging)
        print(f"📝 Using preferences from: {used_file}")
        
        return content
    
    def load_nih_research_summary(self) -> str:
        """Load NIH research summary for context"""
        try:
            with open('nih_polarized_training_summary.md', 'r') as f:
                return f.read()
        except FileNotFoundError:
            return "NIH research summary not available."
    
    def create_training_context(self, training_data: Dict) -> str:
        """Create comprehensive training context for AI"""
        context = []
        
        # Calculate distribution from activities (same as webpage) instead of using pre-calculated distribution
        activities = training_data.get('activities', [])
        
        # Filter to last 14 days for AI recommendations (consistent time window)
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=14)
        
        recent_activities = []
        for activity in activities:
            if 'date' in activity:
                try:
                    activity_date = datetime.fromisoformat(activity['date'].replace('Z', '+00:00'))
                    if activity_date >= cutoff_date:
                        recent_activities.append(activity)
                except:
                    # If date parsing fails, include the activity
                    recent_activities.append(activity)
        
        # Calculate zone percentages using same method as webpage
        total_zone1_minutes = 0
        total_zone2_minutes = 0
        total_zone3_minutes = 0
        total_minutes = 0
        
        for activity in recent_activities:
            activity_minutes = activity.get('duration_minutes', 0)
            total_zone1_minutes += activity_minutes * (activity.get('zone1_percent', 0) / 100)
            total_zone2_minutes += activity_minutes * (activity.get('zone2_percent', 0) / 100)
            total_zone3_minutes += activity_minutes * (activity.get('zone3_percent', 0) / 100)
            total_minutes += activity_minutes
        
        # Calculate percentages
        zone1_percent = (total_zone1_minutes / total_minutes * 100) if total_minutes > 0 else 0
        zone2_percent = (total_zone2_minutes / total_minutes * 100) if total_minutes > 0 else 0
        zone3_percent = (total_zone3_minutes / total_minutes * 100) if total_minutes > 0 else 0
        
        # Calculate adherence score (simplified version)
        adherence_score = 100 - (abs(zone1_percent - 80) + abs(zone2_percent - 10) + abs(zone3_percent - 10)) / 2
        adherence_score = max(0, min(100, adherence_score))
        
        # Add current day context for practical scheduling
        from datetime import datetime
        today = datetime.now()
        day_of_week = today.strftime("%A")
        current_date = today.strftime("%Y-%m-%d")
        
        # Check if user already worked out today
        today_workouts = [a for a in recent_activities if a.get('date', '')[:10] == current_date]
        already_worked_out_today = len(today_workouts) > 0
        
        context.append(f"## Current Training Analysis (Last 14 Days)")
        context.append(f"- Total Activities: {len(recent_activities)}")
        context.append(f"- Total Training Time: {total_minutes:.0f} minutes")
        context.append(f"- Today: {day_of_week} ({current_date})")
        context.append(f"- Already worked out today: {'Yes' if already_worked_out_today else 'No'}")
        if already_worked_out_today:
            today_workout_names = [w.get('name', 'Unknown') for w in today_workouts]
            context.append(f"- Today's workouts: {', '.join(today_workout_names)}")
        
        # Debug logging to see what the AI is receiving vs old distribution
        old_dist = training_data.get('distribution', {})
        print(f"🐛 AI Debug - OLD distribution data: Zone1={old_dist.get('zone1_percent', 0):.1f}% Zone2={old_dist.get('zone2_percent', 0):.1f}% Zone3={old_dist.get('zone3_percent', 0):.1f}%")
        print(f"🐛 AI Debug - NEW calculated data: Zone1={zone1_percent:.1f}% Zone2={zone2_percent:.1f}% Zone3={zone3_percent:.1f}%")
        print(f"🐛 AI using {len(recent_activities)} activities from last 14 days")
        
        context.append(f"- Zone 1 (Low): {zone1_percent:.1f}% [Target: 80%] {'❌ BELOW TARGET' if zone1_percent < 80 else '✅ ADEQUATE'}")
        context.append(f"- Zone 2 (Threshold): {zone2_percent:.1f}% [Target: 10%] {'❌ ABOVE TARGET' if zone2_percent > 10 else '✅ ADEQUATE'}")
        context.append(f"- Zone 3 (High): {zone3_percent:.1f}% [Target: 10%] {'❌ ABOVE TARGET' if zone3_percent > 10 else '✅ ADEQUATE'}")
        context.append(f"- Adherence Score: {adherence_score:.1f}/100")
        
        # Calculate weekly volume in hours for training approach guidance
        weekly_hours = total_minutes / 60
        context.append(f"- Weekly Volume: {weekly_hours:.1f} hours")
        
        # Volume-based training approach recommendations
        if weekly_hours < 4:
            context.append(f"📊 VOLUME GUIDANCE: <4 hours/week - Consider basic fitness approach with mixed intensities")
            training_approach = "low-volume"
        elif weekly_hours < 6:
            context.append(f"📊 VOLUME GUIDANCE: {weekly_hours:.1f} hours/week - Pyramidal approach may be better (70% Z1, 20% Z2, 10% Z3)")
            training_approach = "pyramidal"
        else:
            context.append(f"📊 VOLUME GUIDANCE: {weekly_hours:.1f} hours/week - Sufficient volume for polarized training (80% Z1, 10% Z2, 10% Z3)")
            training_approach = "polarized"
        
        # Add explicit training guidance based on volume and current distribution
        if zone3_percent >= 10:
            context.append(f"⚠️ CRITICAL: Zone 3 is ALREADY at {zone3_percent:.1f}% (target is 10%). ABSOLUTELY NO high-intensity workouts!")
            context.append(f"🚫 ZONE 3 PROHIBITION: Current Z3 = {zone3_percent:.1f}% ≥ 10% target. Focus ONLY on Zone 1 aerobic base.")
        elif zone3_percent >= 8:
            context.append(f"⚠️ CAUTION: Zone 3 is at {zone3_percent:.1f}% (close to 10% target). Avoid high-intensity unless absolutely necessary.")
            
        if zone1_percent < 80 and training_approach == "polarized":
            context.append(f"🎯 PRIORITY: Increase Zone 1 from {zone1_percent:.1f}% to 80%. Focus on aerobic base building.")
        elif zone1_percent < 70 and training_approach == "pyramidal":
            context.append(f"🎯 PRIORITY: Increase Zone 1 from {zone1_percent:.1f}% to 70% (pyramidal approach for your volume).")
        
        # Add volume context to the analysis
        context.append(f"- Training Approach: {training_approach.upper()} (based on {weekly_hours:.1f} hrs/week)")
        
        # Recent activities
        activities = training_data.get('activities', [])[-5:]  # Last 5 activities
        if activities:
            context.append(f"\\n## Recent Activities")
            for activity in activities:
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
    
    def generate_ai_recommendations(self, training_data: Dict, 
                                  num_recommendations: int = 3,
                                  max_retries: int = 3) -> List[AIWorkoutRecommendation]:
        """Generate AI-powered workout recommendations"""
        
        # Load context
        user_preferences = self.load_user_preferences()
        nih_research = self.load_nih_research_summary()
        training_context = self.create_training_context(training_data)
        
        # Create comprehensive prompt
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

🚫 BEFORE RECOMMENDING ANY HIGH-INTENSITY WORKOUT: Double-check if Zone 3 percentage is ≥10%. If yes, recommend Zone 1 aerobic base instead.

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
   - **<4 hours/week**: Mixed approach, focus on general fitness
   - **4-6 hours/week**: PYRAMIDAL approach (70% Z1, 20% Z2, 10% Z3) - More Zone 2 threshold work
   - **>6 hours/week**: POLARIZED approach (80% Z1, 10% Z2, 10% Z3) - Minimal Zone 2
3. Current training distribution vs. volume-appropriate targets:
   - **Polarized (>6 hrs/week)**: If Zone 1 < 80% OR Zone 3 > 10%, focus on Zone 1
   - **Pyramidal (4-6 hrs/week)**: If Zone 1 < 70% OR Zone 2 < 20%, adjust accordingly
   - Only recommend Zone 3 if current Zone 3 is significantly below target
4. Equipment preferences (Peloton, RowERG, dumbbells)
5. Recovery needs based on recent training
6. Progressive overload principles
7. Variety to prevent boredom
8. Use correct zone terminology for each activity type

CRITICAL RULES - READ CAREFULLY:
- **Volume determines training approach**: Use pyramidal targets for <6 hrs/week, polarized for >6 hrs/week
- **🚫 ZONE 3 PROHIBITION**: If current Zone 3 ≥ 10%, DO NOT recommend ANY high-intensity workouts (Power Zone 5-6, VO2 max, HIIT, intervals above threshold)
- **ZONE 3 MATH CHECK**: If Zone 3 percentage is 10.0% or higher, the athlete has ENOUGH high-intensity. Focus on Zone 1 only.
- **Zone 2 threshold work**: More appropriate for pyramidal (limited volume) athletes
- **When Zone 3 is adequate**: Only recommend Zone 1 (aerobic base) and Zone 2 (threshold) workouts
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
        
        for attempt in range(max_retries):
            try:
                # Use fallback model on the last attempt if o3 keeps failing
                current_model = self.fallback_model if attempt == max_retries - 1 else self.model
                print(f"🤖 Calling OpenAI {current_model} model (attempt {attempt + 1}/{max_retries})...")
                
                if attempt == 0:  # Only log prompt details on first attempt
                    print(f"📝 Prompt length: {len(prompt)} characters")
                    print(f"📋 Prompt preview (first 500 chars):\n{prompt[:500]}...")
                    print(f"📋 Prompt ending (last 200 chars):\n...{prompt[-200:]}")
                
                # Use temperature for fallback model since o3 doesn't support it
                api_params = {
                    "model": current_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_completion_tokens": 2000 if current_model == "o3" else None
                }
                
                if current_model != "o3":
                    api_params["max_tokens"] = 2000
                    api_params["temperature"] = 0.7
                    del api_params["max_completion_tokens"]
                
                response = self.client.chat.completions.create(**api_params)
                
                print(f"✅ OpenAI response received")
                print(f"Response object type: {type(response)}")
                print(f"Response choices length: {len(response.choices) if response.choices else 0}")
                
                if not response.choices or not response.choices[0].message:
                    raise ValueError("OpenAI returned no message content")
                
                # Parse the JSON response
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
                if recommendations_json.startswith('```json'):
                    recommendations_json = recommendations_json[7:]
                if recommendations_json.endswith('```'):
                    recommendations_json = recommendations_json[:-3]
                
                recommendations_json = recommendations_json.strip()
                
                if not recommendations_json:
                    if attempt < max_retries - 1:
                        print(f"⚠️  Empty response, retrying...")
                        continue
                    else:
                        raise ValueError("AI returned empty response after all retries")
                
                recommendations_data = json.loads(recommendations_json)
                
                # Convert to AIWorkoutRecommendation objects
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
                
                print(f"✅ Successfully generated {len(ai_recommendations)} recommendations")
                return ai_recommendations
                
            except json.JSONDecodeError as e:
                if attempt < max_retries - 1:
                    print(f"⚠️  JSON decode error, retrying: {e}")
                    continue
                else:
                    print(f"❌ JSON decode failed after all retries: {e}")
                    raise e
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️  Error on attempt {attempt + 1}, retrying: {e}")
                    continue
                else:
                    print(f"❌ All retry attempts failed: {e}")
                    raise e
        
        # If we get here, all retries failed
        print(f"❌ All {max_retries} attempts failed, returning fallback")
        return [AIWorkoutRecommendation(
            workout_type="Fallback Workout",
            duration_minutes=60,
            description="Easy aerobic workout",
            structure="60 minutes easy pace in Zone 1",
            reasoning=f"AI service unavailable after {max_retries} attempts",
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