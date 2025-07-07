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
    
    def load_user_preferences(self) -> str:
        """Load user workout preferences from markdown file"""
        try:
            with open('workout_preferences.md', 'r') as f:
                content = f.read()
                
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
                
                return content
        except FileNotFoundError:
            return "No user preferences file found. Using general recommendations."
    
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
        
        # Current training distribution
        dist = training_data.get('distribution', {})
        context.append(f"## Current Training Analysis (Last 14 Days)")
        context.append(f"- Total Activities: {dist.get('total_activities', 0)}")
        context.append(f"- Total Training Time: {dist.get('total_minutes', 0)} minutes")
        context.append(f"- Zone 1 (Low): {dist.get('zone1_percent', 0):.1f}% [Target: 80%]")
        context.append(f"- Zone 2 (Threshold): {dist.get('zone2_percent', 0):.1f}% [Target: 10%]")
        context.append(f"- Zone 3 (High): {dist.get('zone3_percent', 0):.1f}% [Target: 10%]")
        context.append(f"- Adherence Score: {dist.get('adherence_score', 0):.1f}/100")
        
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
                                  num_recommendations: int = 3) -> List[AIWorkoutRecommendation]:
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
Generate {num_recommendations} specific, actionable workout recommendations for the next week. 
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
2. Current training distribution vs. polarized training targets
3. Equipment preferences (Peloton, RowERG, dumbbells)
4. Recovery needs based on recent training
5. Progressive overload principles
6. Variety to prevent boredom
7. Use correct zone terminology for each activity type

Return only a JSON array of workout recommendations, no other text.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=2000
            )
            
            # Parse the JSON response
            recommendations_json = response.choices[0].message.content.strip()
            
            # Debug logging
            print(f"AI Response length: {len(recommendations_json)} characters")
            if len(recommendations_json) < 10:
                print(f"AI Response content: {repr(recommendations_json)}")
            
            # Clean up response (remove code blocks if present)
            if recommendations_json.startswith('```json'):
                recommendations_json = recommendations_json[7:]
            if recommendations_json.endswith('```'):
                recommendations_json = recommendations_json[:-3]
            
            recommendations_json = recommendations_json.strip()
            
            if not recommendations_json:
                raise ValueError("AI returned empty response")
            
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
            
            return ai_recommendations
            
        except Exception as e:
            print(f"Error generating AI recommendations: {e}")
            # Return fallback recommendation
            return [AIWorkoutRecommendation(
                workout_type="Fallback Workout",
                duration_minutes=60,
                description="Easy aerobic workout",
                structure="60 minutes easy pace in Zone 1",
                reasoning=f"AI service unavailable: {str(e)}",
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