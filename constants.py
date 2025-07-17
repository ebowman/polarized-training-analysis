"""
Constants Module for PolarFlow Training Analysis

This module centralizes all magic numbers used throughout the application
for better maintainability and clarity. Constants are grouped by their
functional area and include descriptive names and comments.
"""

# ============================================================================
# TRAINING ZONE DISTRIBUTION CONSTANTS
# ============================================================================

# Polarized training zone distribution percentages (80/10/10 approach)
POLARIZED_ZONE1_TARGET_PERCENT = 80.0  # Low intensity target (aerobic base)
POLARIZED_ZONE2_TARGET_PERCENT = 10.0  # Threshold intensity target
POLARIZED_ZONE3_TARGET_PERCENT = 10.0  # High intensity target

# Pyramidal training zone distribution percentages (70/20/10 approach)
PYRAMIDAL_ZONE1_TARGET_PERCENT = 70.0  # Low intensity for pyramidal
PYRAMIDAL_ZONE2_TARGET_PERCENT = 20.0  # More threshold work in pyramidal
PYRAMIDAL_ZONE3_TARGET_PERCENT = 10.0  # Same high intensity as polarized

# ============================================================================
# HEART RATE ZONE MULTIPLIERS (Based on LTHR)
# ============================================================================

# These multipliers are applied to LTHR (Lactate Threshold Heart Rate)
# to calculate the 7-zone heart rate model boundaries
HR_ZONE1_MAX_MULTIPLIER = 0.81    # Zone 1 Recovery: <81% LTHR
HR_ZONE2_MAX_MULTIPLIER = 0.89    # Zone 2 Aerobic: 81-89% LTHR
HR_ZONE3_MAX_MULTIPLIER = 0.93    # Zone 3 Tempo: 90-93% LTHR
HR_ZONE4_MAX_MULTIPLIER = 0.99    # Zone 4 Threshold: 94-99% LTHR
HR_ZONE5A_MAX_MULTIPLIER = 1.02   # Zone 5a VO2max: 100-102% LTHR
HR_ZONE5B_MAX_MULTIPLIER = 1.06   # Zone 5b Anaerobic: 103-106% LTHR
HR_ZONE5C_MIN_MULTIPLIER = 1.06   # Zone 5c Neuromuscular: >106% LTHR

# Fallback: Max HR multipliers for 3-zone model when LTHR not available
HR_ZONE1_MAX_HR_MULTIPLIER = 0.82  # ~82% max HR
HR_ZONE2_MAX_HR_MULTIPLIER = 0.87  # ~87% max HR
LTHR_FROM_MAX_HR_MULTIPLIER = 0.90 # Estimate LTHR as ~90% of max HR

# ============================================================================
# POWER ZONE MULTIPLIERS (Based on FTP)
# ============================================================================

# Coggan power zone model multipliers applied to FTP
# (Functional Threshold Power)
POWER_ZONE1_MAX_MULTIPLIER = 0.55   # Zone 1 Recovery: <55% FTP
POWER_ZONE2_MAX_MULTIPLIER = 0.75   # Zone 2 Endurance: 56-75% FTP
POWER_ZONE3_MAX_MULTIPLIER = 0.90   # Zone 3 Tempo: 76-90% FTP
POWER_ZONE4_MAX_MULTIPLIER = 1.05   # Zone 4 Threshold: 91-105% FTP
POWER_ZONE5_MAX_MULTIPLIER = 1.20   # Zone 5 VO2max: 106-120% FTP
POWER_ZONE6_MAX_MULTIPLIER = 1.50   # Zone 6 Anaerobic: 121-150% FTP
POWER_ZONE7_MIN_MULTIPLIER = 1.50   # Zone 7 Neuromuscular: >150% FTP

# FTP calculation from 20-minute test
FTP_FROM_20MIN_TEST_MULTIPLIER = 0.95  # FTP = 95% of 20-min average power

# ============================================================================
# TRAINING VOLUME CONSTANTS
# ============================================================================

# Weekly volume thresholds (in hours)
LOW_VOLUME_THRESHOLD_HOURS = 4.0      # Below this: low volume approach
PYRAMIDAL_VOLUME_THRESHOLD_HOURS = 6.0 # Below this: consider pyramidal
MIN_WEEKLY_VOLUME_MINUTES = 180       # Minimum 3 hours/week for meaningful training

# Workout duration recommendations (in minutes)
MIN_ZONE3_MINUTES_PER_WEEK = 30      # Minimum high-intensity per week
DEFAULT_EASY_WORKOUT_MINUTES = 60     # Standard easy aerobic workout
DEFAULT_INTERVAL_WORKOUT_MINUTES = 75  # Standard interval session
DEFAULT_LONG_WORKOUT_MINUTES = 120    # Long aerobic workout
DEFAULT_RECOVERY_WORKOUT_MINUTES = 45 # Active recovery session

# ============================================================================
# ANALYSIS WINDOW CONSTANTS
# ============================================================================

# Time windows for various analyses (in days)
ANALYSIS_WINDOW_DAYS = 14             # Research-based 14-day analysis window
ZONE3_RECENT_DAYS = 3                 # Check Zone 3 accumulation over 3 days
INTENSITY_SPACING_DAYS = 4            # Minimum days between high-intensity sessions
CONSECUTIVE_TRAINING_WARNING_DAYS = 5 # Warn after 5 consecutive training days
RECENT_DATA_STALENESS_DAYS = 7       # Data considered stale after 7 days

# ============================================================================
# WEB SERVER CONSTANTS
# ============================================================================

# Cache durations (in seconds)
CACHE_DURATION_SECONDS = 300          # 5 minutes cache for training data
AI_SESSION_EXPIRY_SECONDS = 3600      # 1 hour expiry for AI sessions

# Server configuration
DEFAULT_WEB_PORT = 8080               # Default port for web server
DEFAULT_HOST = "127.0.0.1"           # Default host binding

# ============================================================================
# DEVIATION AND SCORING CONSTANTS
# ============================================================================

# Zone deviation weights for adherence scoring
ZONE1_DEVIATION_WEIGHT = 0.5         # Zone 1 most important (50% weight)
ZONE2_DEVIATION_WEIGHT = 0.25        # Zone 2 moderate importance (25% weight)
ZONE3_DEVIATION_WEIGHT = 0.25        # Zone 3 moderate importance (25% weight)

# Adherence score thresholds
EXCELLENT_ADHERENCE_SCORE = 80       # 80+ is excellent adherence
GOOD_ADHERENCE_SCORE = 60           # 60-79 is good adherence

# Zone percentage thresholds for recommendations
ZONE1_LOW_WARNING_PERCENT = 75       # Warn if Zone 1 below 75%
ZONE2_HIGH_WARNING_PERCENT = 20      # Warn if Zone 2 above 20%
ZONE3_LOW_WARNING_PERCENT = 5        # Suggest more if Zone 3 below 5%
ZONE3_HIGH_WARNING_PERCENT = 15      # Warn if Zone 3 above 15%

# ============================================================================
# WORKOUT RECOMMENDATION CONSTANTS
# ============================================================================

# Volume increase factors
VOLUME_DEFICIT_WORKOUT_FACTOR = 0.6  # Add 60% of deficit in one workout
WEEKLY_VOLUME_LONG_WORKOUT_FACTOR = 0.4  # Long workout = 40% of weekly volume
WEEKLY_VOLUME_EASY_WORKOUT_FACTOR = 0.25  # Easy workout = 25% of weekly volume

# Intensity thresholds
ZONE3_SIGNIFICANT_PERCENT = 15       # Workout with >15% Zone 3 is "intense"
ZONE3_OVERLOAD_PERCENT = 15          # >15% Zone 3 in 3 days = overload
ZONE3_CLOSE_TO_TARGET_PERCENT = 8    # 8% is close to 10% target

# ============================================================================
# AI RECOMMENDATION CONSTANTS
# ============================================================================

# Training approach decision thresholds
MIN_ADHERENCE_FOR_LOW_VOLUME = 50.0  # Minimum adherence score for low volume
GOOD_ADHERENCE_FOR_LOW_VOLUME = 75.0 # Good adherence for low volume training

# Zone deficit/excess thresholds for AI decisions
ZONE1_SIGNIFICANT_DEFICIT = 10       # >10% below target is significant
ZONE2_EXCESS_THRESHOLD = 5           # >5% above target needs correction
ZONE3_DEFICIT_THRESHOLD = 3          # >3% below target may need intensity

# ============================================================================
# DEFAULT ENVIRONMENT VALUES
# ============================================================================

# Default physiological values if not set in environment
DEFAULT_MAX_HEART_RATE = 180         # Default max HR if not configured
DEFAULT_FTP_WATTS = 250              # Default FTP if not configured
DEFAULT_LTHR = 0                     # Default 0 indicates LTHR not set