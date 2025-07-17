# Configuration Migration Report

Generated: 2025-07-17T20:48:06.142947

## Summary

- Files analyzed: 17
- Environment accesses: 45
- Hardcoded values: 33
- Sport config usages: 55

## Detailed Findings

### ai_providers.py

#### Environment Variable Access
- Line 46: `OPENAI_API_KEY` - `self.api_key = os.getenv("OPENAI_API_KEY")`
- Line 112: `ANTHROPIC_API_KEY` - `self.api_key = os.getenv("ANTHROPIC_API_KEY")`
- Line 199: `AI_PROVIDER` - `provider_name = os.getenv("AI_PROVIDER", "auto").lower()`

### ai_recommendations.py

#### Environment Variable Access
- Line 21: `USE_SPORT_CONFIG` - `USE_SPORT_CONFIG = os.getenv('USE_SPORT_CONFIG', 'true').lower() == 'true'`
- Line 499: `AVERAGE_FTP_HR` - `lthr = int(os.getenv("AVERAGE_FTP_HR", "0"))`
- Line 550: `AVERAGE_FTP_HR` - `lthr = int(os.getenv("AVERAGE_FTP_HR", "0"))`
- Line 564: `MAX_HEART_RATE` - `max_hr = int(os.getenv("MAX_HEART_RATE", "171"))`
- Line 565: `AVERAGE_FTP_HR` - `lthr = int(os.getenv("AVERAGE_FTP_HR", "0"))`

#### Hardcoded Values
- Line 473: `1` - `- Power Zone 1-2 (0-75% FTP / 0-{int(ftp * 0.75)}W) = Polarized Zone 1`
- Line 474: `2` - `- Power Zone 3-4 (76-105% FTP / {int(ftp * 0.76)}-{int(ftp * 1.05)}W) = Polarized Zone 2`
- Line 475: `3` - `- Power Zone 5-7 (106%+ FTP / >{int(ftp * 1.06)}W) = Polarized Zone 3""")`
- Line 816: `1` - `- Power Zone 1-2 (0-75% FTP) = Polarized Zone 1 (aerobic base)`
- Line 817: `2` - `- Power Zone 3-4 (76-105% FTP) = Polarized Zone 2 (threshold)`
- Line 818: `3` - `- Power Zone 5-7 (106%+ FTP) = Polarized Zone 3 (high intensity)`

#### Sport Config Usage
- Line 94: `self.sport_config_service = SportConfigService()`
- Line 105: `for sport in self.sport_config_service.get_all_sports():`
- Line 204: `targets = self.sport_config_service.get_zone_distribution_target()`
- Line 402: `self.sport_config_service = SportConfigService()`
- Line 413: `for sport in self.sport_config_service.get_all_sports():`
- Line 505: `rowing_sport = self.sport_config_service.get_sport_by_name('Rowing')`
- Line 507: `threshold = self.sport_config_service.get_threshold_value(rowing_sport, MetricType.HEART_RATE)`
- Line 509: `zones = self.sport_config_service.calculate_zones(rowing_sport, MetricType.HEART_RATE, threshold)`

### config_manager.py

#### Sport Config Usage
- Line 259: `return self._sport_config_service.get_sport_by_name(sport_name)`
- Line 265: `return self._sport_config_service.get_sport_by_activity_type(activity_type)`

### config_migration.py

#### Sport Config Usage
- Line 64: `self.config_service = SportConfigService()`
- Line 284: `service = SportConfigService()`

### config_migration_helper.py

#### Hardcoded Values
- Line 40: `w` - `re.compile(r'DEFAULT_.*=.*["\']?(\w+)["\']?')`

### constants.py

#### Hardcoded Values
- Line 40: `0` - `LTHR_FROM_MAX_HR_MULTIPLIER = 0.90 # Estimate LTHR as ~90% of max HR`
- Line 57: `0` - `FTP_FROM_20MIN_TEST_MULTIPLIER = 0.95  # FTP = 95% of 20-min average power`
- Line 70: `t` - `DEFAULT_EASY_WORKOUT_MINUTES = 60     # Standard easy aerobic workout`
- Line 71: `n` - `DEFAULT_INTERVAL_WORKOUT_MINUTES = 75  # Standard interval session`
- Line 72: `t` - `DEFAULT_LONG_WORKOUT_MINUTES = 120    # Long aerobic workout`
- Line 73: `n` - `DEFAULT_RECOVERY_WORKOUT_MINUTES = 45 # Active recovery session`
- Line 95: `r` - `DEFAULT_WEB_PORT = 8080               # Default port for web server`
- Line 96: `g` - `DEFAULT_HOST = "127.0.0.1"           # Default host binding`
- Line 149: `0` - `DEFAULT_MAX_HEART_RATE = 180         # Default max HR if not configured`
- Line 149: `d` - `DEFAULT_MAX_HEART_RATE = 180         # Default max HR if not configured`
- Line 150: `0` - `DEFAULT_FTP_WATTS = 250              # Default FTP if not configured`
- Line 150: `d` - `DEFAULT_FTP_WATTS = 250              # Default FTP if not configured`
- Line 151: `0` - `DEFAULT_LTHR = 0                     # Default 0 indicates LTHR not set`
- Line 151: `t` - `DEFAULT_LTHR = 0                     # Default 0 indicates LTHR not set`

### demo_config_manager.py

#### Environment Variable Access
- Line 47: `FTP` - `os.environ['FTP'] = '275'`
- Line 59: `FTP` - `del os.environ['FTP']`
- Line 260: `MAX_HEART_RATE` - `old_max_hr = os.getenv('MAX_HEART_RATE', '180')`
- Line 262: `MAX_HEART_RATE` - `print(f"  Old: os.getenv('MAX_HEART_RATE', '180') = {old_max_hr}")`
- Line 266: `FTP` - `old_ftp = int(os.getenv('FTP', '250'))`
- Line 268: `FTP` - `print(f"  Old: int(os.getenv('FTP', '250')) = {old_ftp}")`

#### Hardcoded Values
- Line 46: `5` - `print("1. Setting FTP=275 via environment variable...")`
- Line 47: `5` - `os.environ['FTP'] = '275'`
- Line 53: `5` - `print("2. Setting FTP=285 via runtime...")`

### logging_config.py

#### Environment Variable Access
- Line 161: `POLARFLOW_LOG_LEVEL` - `log_level=os.getenv("POLARFLOW_LOG_LEVEL", "INFO"),`
- Line 162: `POLARFLOW_ENABLE_FILE_LOGGING` - `enable_file_logging=os.getenv("POLARFLOW_ENABLE_FILE_LOGGING", "true").lower() == "true"`

### strava_client.py

#### Environment Variable Access
- Line 40: `STRAVA_CLIENT_ID` - `self.client_id = os.getenv("STRAVA_CLIENT_ID")`
- Line 41: `STRAVA_CLIENT_SECRET` - `self.client_secret = os.getenv("STRAVA_CLIENT_SECRET")`

### test_backward_compatibility.py

#### Environment Variable Access
- Line 13: `USE_SPORT_CONFIG` - `os.environ['USE_SPORT_CONFIG'] = 'false'`
- Line 47: `USE_SPORT_CONFIG` - `os.environ['USE_SPORT_CONFIG'] = 'true'`

### test_zone_calculator.py

#### Hardcoded Values
- Line 222: `0` - `zones = strategy.calculate_zones(160)  # LTHR = 160`
- Line 235: `0` - `zones = strategy.calculate_zones(250)  # FTP = 250`

### tests/test_config_manager.py

#### Environment Variable Access
- Line 63: `MAX_HEART_RATE` - `os.environ['MAX_HEART_RATE'] = '190'`
- Line 64: `FTP` - `os.environ['FTP'] = '300'`
- Line 73: `MAX_HEART_RATE` - `del os.environ['MAX_HEART_RATE']`
- Line 74: `FTP` - `del os.environ['FTP']`
- Line 215: `FTP` - `os.environ['FTP'] = '300'`
- Line 232: `FTP` - `del os.environ['FTP']`
- Line 325: `MAX_HEART_RATE` - `os.environ['MAX_HEART_RATE'] = '195'`
- Line 326: `AVERAGE_FTP_HR` - `os.environ['AVERAGE_FTP_HR'] = '170'`
- Line 336: `MAX_HEART_RATE` - `del os.environ['MAX_HEART_RATE']`
- Line 337: `AVERAGE_FTP_HR` - `del os.environ['AVERAGE_FTP_HR']`

#### Hardcoded Values
- Line 63: `0` - `os.environ['MAX_HEART_RATE'] = '190'`
- Line 64: `0` - `os.environ['FTP'] = '300'`
- Line 79: `0` - `f.write('TEST_MAX_HEART_RATE=200\n')`
- Line 80: `0` - `f.write('TEST_FTP=350\n')`
- Line 215: `0` - `os.environ['FTP'] = '300'`
- Line 325: `5` - `os.environ['MAX_HEART_RATE'] = '195'`
- Line 326: `0` - `os.environ['AVERAGE_FTP_HR'] = '170'`

### tests/test_error_conditions.py

#### Sport Config Usage
- Line 203: `service = SportConfigService()`
- Line 227: `service = SportConfigService()`
- Line 251: `service = SportConfigService()`

### tests/test_sport_config.py

#### Sport Config Usage
- Line 280: `return SportConfigService()`
- Line 580: `service = SportConfigService()`

### training_analysis.py

#### Environment Variable Access
- Line 26: `USE_SPORT_CONFIG` - `USE_SPORT_CONFIG = os.getenv('USE_SPORT_CONFIG', 'true').lower() == 'true'`
- Line 168: `MAX_HEART_RATE` - `self.max_hr = max_hr or int(os.getenv("MAX_HEART_RATE", "180"))`
- Line 169: `AVERAGE_FTP_HR` - `self.lthr = lthr or int(os.getenv("AVERAGE_FTP_HR", "0"))`
- Line 170: `AVERAGE_FTP_POWER` - `self.ftp_power = ftp_power or int(os.getenv("AVERAGE_FTP_POWER", "0"))`
- Line 176: `FTP` - `self.ftp = ftp or int(os.getenv("FTP", "250"))`

#### Sport Config Usage
- Line 182: `self.sport_config_service = SportConfigService()`
- Line 185: `self.sport_config_service.update_threshold('lthr', self.lthr)`
- Line 187: `self.sport_config_service.update_threshold('ftp', self.ftp)`
- Line 188: `self.sport_config_service.update_threshold('max_hr', self.max_hr)`
- Line 203: `targets = self.sport_config_service.get_zone_distribution_target()`
- Line 240: `sport = self.sport_config_service.get_sport_by_activity_type(sport_type)`
- Line 243: `threshold = self.sport_config_service.get_threshold_value(sport, MetricType.HEART_RATE)`
- Line 245: `zones = self.sport_config_service.calculate_zones(sport, MetricType.HEART_RATE, threshold)`
- Line 270: `sport = self.sport_config_service.get_sport_by_activity_type(sport_type)`
- Line 273: `threshold = self.sport_config_service.get_threshold_value(sport, MetricType.POWER)`
- Line 275: `zones = self.sport_config_service.calculate_zones(sport, MetricType.POWER, threshold)`
- Line 318: `sport = self.sport_config_service.get_sport_by_activity_type(sport_type)`
- Line 470: `sport = self.sport_config_service.get_sport_by_activity_type(sport_type)`
- Line 564: `sport = self.sport_config_service.get_sport_by_activity_type(sport_type)`
- Line 628: `sport = self.sport_config_service.get_sport_by_activity_type(sport_type)`
- Line 638: `supported_metrics = self.sport_config_service.get_supported_metrics(sport)`

### web_server.py

#### Environment Variable Access
- Line 33: `USE_SPORT_CONFIG` - `USE_SPORT_CONFIG = os.getenv('USE_SPORT_CONFIG', 'true').lower() == 'true'`
- Line 41: `FLASK_SECRET_KEY` - `app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')`
- Line 261: `MAX_HEART_RATE` - `max_hr = int(os.getenv('MAX_HEART_RATE', 171))`
- Line 262: `FTP` - `ftp = int(os.getenv('FTP', 301))`
- Line 263: `AVERAGE_FTP_HR` - `lthr = int(os.getenv('AVERAGE_FTP_HR', '0'))`
- Line 1128: `OPENAI_API_KEY` - `'ai_enabled': os.getenv('OPENAI_API_KEY') is not None`

#### Sport Config Usage
- Line 278: `sport_config_service = SportConfigService()`
- Line 288: `philosophy = sport_config_service.get_training_philosophy()`
- Line 289: `zone_targets = sport_config_service.get_zone_distribution_target()`
- Line 305: `sport_config_service.update_threshold('lthr', lthr)`
- Line 306: `sport_config_service.update_threshold('ftp', ftp)`
- Line 307: `sport_config_service.update_threshold('max_hr', max_hr)`
- Line 312: `cycling_sport = sport_config_service.get_sport_by_name('Cycling')`
- Line 314: `power_zones_data = sport_config_service.calculate_zones(cycling_sport, MetricType.POWER, ftp)`
- Line 331: `rowing_sport = sport_config_service.get_sport_by_name('Rowing')`
- Line 334: `hr_zones_data = sport_config_service.calculate_zones(rowing_sport, MetricType.HEART_RATE, threshold)`

### zone_calculator.py

#### Environment Variable Access
- Line 28: `USE_SPORT_CONFIG` - `USE_SPORT_CONFIG = os.getenv('USE_SPORT_CONFIG', 'true').lower() == 'true'`
- Line 163: `MAX_HEART_RATE` - `self.max_hr = max_hr if max_hr is not None else int(os.getenv("MAX_HEART_RATE", "180"))`
- Line 164: `AVERAGE_FTP_HR` - `self.lthr = lthr if lthr is not None else int(os.getenv("AVERAGE_FTP_HR", "0"))`
- Line 165: `FTP` - `self.ftp = ftp if ftp is not None else int(os.getenv("FTP", "250"))`

#### Sport Config Usage
- Line 176: `self.sport_config_service = SportConfigService()`
- Line 280: `sport = self.sport_config_service.get_sport_by_activity_type(sport_type)`
- Line 346: `return self.sport_config_service.get_zone_distribution_target()`
- Line 423: `self.sport_config_service.update_threshold('max_hr', max_hr)`
- Line 425: `self.sport_config_service.update_threshold('lthr', lthr)`
- Line 427: `self.sport_config_service.update_threshold('ftp', ftp)`
- Line 437: `sport = self.sport_config_service.get_sport_by_activity_type(sport_type)`
- Line 441: `threshold = self.sport_config_service.get_threshold_value(sport, metric_type)`
- Line 445: `zones = self.sport_config_service.calculate_zones(sport, metric_type, threshold)`
- Line 462: `sport = self.sport_config_service.get_sport_by_activity_type(sport_type)`
- Line 466: `threshold = self.sport_config_service.get_threshold_value(sport, metric_type)`
- Line 470: `zones = self.sport_config_service.calculate_zones(sport, metric_type, threshold)`

## Migration Recommendations

1. Replace `os.getenv()` calls with `config_manager.get()`
2. Move hardcoded defaults to `DefaultConfigSource`
3. Ensure backward compatibility by maintaining environment variable names
4. Update imports to use `from config_manager import get_config`
