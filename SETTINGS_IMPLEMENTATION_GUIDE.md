# Settings Page Implementation Guide

## Quick Start for Developers

### 1. File Structure to Create
```
polarized-training-analysis/
├── templates/
│   └── settings.html          # New settings page template
├── static/
│   ├── js/
│   │   └── settings.js        # Settings page JavaScript
│   └── css/
│       └── settings.css       # Settings page styles
├── settings_service.py        # New backend service
└── settings_routes.py         # New Flask routes (or add to web_server.py)
```

### 2. Backend Implementation Steps

#### Step 1: Create Settings Service (settings_service.py)
```python
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import dotenv_values, set_key
from sport_config_service import SportConfigService
from logging_config import get_logger

logger = get_logger(__name__)

class SettingsService:
    """Manages all application settings"""
    
    def __init__(self):
        self.env_path = Path(".env")
        self.sport_config_service = SportConfigService()
        self.backup_dir = Path("backups/settings")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings from various sources"""
        return {
            "env": self._get_env_settings(),
            "sportConfig": self._get_sport_config(),
            "prompts": self._get_prompt_templates(),
            "status": self._get_system_status()
        }
    
    def update_env_settings(self, updates: Dict[str, str]) -> bool:
        """Update .env file with new values"""
        try:
            # Create backup first
            self._backup_file(self.env_path)
            
            # Update each key
            for key, value in updates.items():
                # Special handling for API keys
                if "KEY" in key and value.startswith("•"):
                    # Skip masked values
                    continue
                set_key(self.env_path, key, value)
            
            return True
        except Exception as e:
            logger.error(f"Failed to update .env: {e}")
            return False
    
    def _get_env_settings(self) -> Dict[str, Any]:
        """Read and structure .env settings"""
        env_values = dotenv_values(self.env_path)
        
        return {
            "strava": {
                "clientId": env_values.get("STRAVA_CLIENT_ID", ""),
                "clientSecret": self._mask_secret(env_values.get("STRAVA_CLIENT_SECRET", ""))
            },
            "training": {
                "maxHeartRate": int(env_values.get("MAX_HEART_RATE", 0)),
                "ftp": int(env_values.get("FTP", 0)),
                "lthr": int(env_values.get("AVERAGE_FTP_HR", 0)),
                "maxFtpHr": int(env_values.get("MAX_FTP_HR", 0)),
                "averageFtpPower": int(env_values.get("AVERAGE_FTP_POWER", 0))
            },
            "ai": {
                "provider": env_values.get("AI_PROVIDER", "auto"),
                "primaryProvider": env_values.get("AI_PRIMARY_PROVIDER", "openai"),
                "fallbackProvider": env_values.get("AI_FALLBACK_PROVIDER", "claude"),
                "openaiKey": self._mask_api_key(env_values.get("OPENAI_API_KEY", "")),
                "anthropicKey": self._mask_api_key(env_values.get("ANTHROPIC_API_KEY", ""))
            }
        }
    
    def _mask_secret(self, secret: str) -> str:
        """Mask secret showing only last 4 characters"""
        if not secret or len(secret) < 8:
            return secret
        return "•" * (len(secret) - 4) + secret[-4:]
    
    def _mask_api_key(self, key: str) -> str:
        """Mask API key showing only last 4 characters"""
        if not key or len(key) < 8:
            return key
        return "•" * (len(key) - 4) + key[-4:]
```

#### Step 2: Add Routes to web_server.py
```python
# Add these routes to web_server.py

@app.route('/settings')
def settings_page():
    """Render settings page"""
    return render_template('settings.html')

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get all settings"""
    try:
        settings_service = SettingsService()
        settings = settings_service.get_all_settings()
        return jsonify(settings)
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings/env', methods=['POST'])
def update_env_settings():
    """Update environment settings"""
    try:
        settings_service = SettingsService()
        updates = request.json
        success = settings_service.update_env_settings(updates)
        
        if success:
            return jsonify({"success": True, "message": "Settings updated"})
        else:
            return jsonify({"success": False, "message": "Failed to update settings"}), 500
    except Exception as e:
        logger.error(f"Failed to update env settings: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings/sport-config', methods=['POST'])
def update_sport_config():
    """Update sport configuration"""
    try:
        sport_config_service = SportConfigService()
        config_data = request.json
        
        # Update the configuration
        sport_config_service.update_config(config_data)
        
        return jsonify({"success": True, "message": "Sport config updated"})
    except Exception as e:
        logger.error(f"Failed to update sport config: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings/validate', methods=['POST'])
def validate_settings():
    """Validate settings before saving"""
    try:
        settings = request.json
        errors = []
        
        # Validate Strava settings
        if 'strava' in settings:
            if not settings['strava'].get('clientId'):
                errors.append("Strava Client ID is required")
            if not settings['strava'].get('clientSecret'):
                errors.append("Strava Client Secret is required")
        
        # Validate training settings
        if 'training' in settings:
            hr = settings['training'].get('maxHeartRate', 0)
            if hr < 100 or hr > 220:
                errors.append("Max Heart Rate must be between 100-220")
            
            ftp = settings['training'].get('ftp', 0)
            if ftp < 0 or ftp > 600:
                errors.append("FTP must be between 0-600")
        
        if errors:
            return jsonify({"valid": False, "errors": errors})
        else:
            return jsonify({"valid": True})
            
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 500
```

### 3. Frontend Implementation

#### Step 1: Create settings.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Settings - PolarFlow</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/settings.css') }}">
</head>
<body>
    <div class="settings-container">
        <!-- Header -->
        <div class="settings-header">
            <h1>PolarFlow Settings</h1>
            <button class="close-btn" onclick="window.location.href='/'">✕</button>
        </div>
        
        <!-- Main Content -->
        <div class="settings-content">
            <!-- Sidebar Navigation -->
            <nav class="settings-nav">
                <a href="#general" class="nav-item active" data-section="general">
                    <span class="icon">⚙️</span> General
                </a>
                <a href="#sports" class="nav-item" data-section="sports">
                    <span class="icon">🚴</span> Sports
                </a>
                <a href="#ai" class="nav-item" data-section="ai">
                    <span class="icon">🤖</span> AI Providers
                </a>
                <a href="#prompts" class="nav-item" data-section="prompts">
                    <span class="icon">📝</span> Prompts
                </a>
                <a href="#advanced" class="nav-item" data-section="advanced">
                    <span class="icon">🔧</span> Advanced
                </a>
            </nav>
            
            <!-- Settings Sections -->
            <div class="settings-sections">
                <!-- General Settings -->
                <section id="general" class="settings-section active">
                    <h2>General Settings</h2>
                    
                    <div class="settings-group">
                        <h3>Strava API Configuration</h3>
                        <div class="form-group">
                            <label for="strava-client-id">Client ID</label>
                            <input type="text" id="strava-client-id" class="form-control">
                            <small class="help-text">Get from Strava API settings</small>
                        </div>
                        <div class="form-group">
                            <label for="strava-client-secret">Client Secret</label>
                            <div class="input-group">
                                <input type="password" id="strava-client-secret" class="form-control">
                                <button class="btn-icon toggle-visibility">👁️</button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="settings-group">
                        <h3>Training Zones Configuration</h3>
                        <div class="form-group">
                            <label for="max-hr">Max Heart Rate</label>
                            <input type="number" id="max-hr" class="form-control" min="100" max="220">
                            <small class="help-text">Your maximum heart rate in BPM</small>
                        </div>
                        <div class="form-group">
                            <label for="ftp">FTP (Functional Threshold Power)</label>
                            <input type="number" id="ftp" class="form-control" min="0" max="600">
                            <small class="help-text">Your FTP in watts</small>
                        </div>
                    </div>
                </section>
                
                <!-- Other sections (sports, ai, prompts, advanced) -->
                <!-- ... -->
            </div>
        </div>
        
        <!-- Footer Actions -->
        <div class="settings-footer">
            <button class="btn btn-primary" id="save-settings">💾 Save Changes</button>
            <button class="btn btn-secondary" id="reset-settings">↩️ Reset</button>
            <button class="btn btn-secondary" id="export-settings">📥 Export</button>
            <span class="status-indicator" id="save-status"></span>
        </div>
    </div>
    
    <script src="{{ url_for('static', filename='js/settings.js') }}"></script>
</body>
</html>
```

#### Step 2: Create settings.js
```javascript
// Settings page JavaScript
class SettingsManager {
    constructor() {
        this.settings = {};
        this.isDirty = false;
        this.currentSection = 'general';
        
        this.init();
    }
    
    async init() {
        await this.loadSettings();
        this.setupEventListeners();
        this.setupNavigation();
    }
    
    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            this.settings = await response.json();
            this.populateForm();
        } catch (error) {
            console.error('Failed to load settings:', error);
            this.showError('Failed to load settings');
        }
    }
    
    populateForm() {
        // Populate General Settings
        if (this.settings.env) {
            // Strava settings
            document.getElementById('strava-client-id').value = 
                this.settings.env.strava.clientId || '';
            document.getElementById('strava-client-secret').value = 
                this.settings.env.strava.clientSecret || '';
            
            // Training settings
            document.getElementById('max-hr').value = 
                this.settings.env.training.maxHeartRate || '';
            document.getElementById('ftp').value = 
                this.settings.env.training.ftp || '';
        }
    }
    
    setupEventListeners() {
        // Save button
        document.getElementById('save-settings').addEventListener('click', () => {
            this.saveSettings();
        });
        
        // Form change detection
        document.querySelectorAll('input, select, textarea').forEach(input => {
            input.addEventListener('change', () => {
                this.isDirty = true;
                this.updateSaveButton();
            });
        });
        
        // Password visibility toggle
        document.querySelectorAll('.toggle-visibility').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const input = e.target.previousElementSibling;
                input.type = input.type === 'password' ? 'text' : 'password';
            });
        });
    }
    
    async saveSettings() {
        // Collect form data
        const updates = {
            STRAVA_CLIENT_ID: document.getElementById('strava-client-id').value,
            STRAVA_CLIENT_SECRET: document.getElementById('strava-client-secret').value,
            MAX_HEART_RATE: document.getElementById('max-hr').value,
            FTP: document.getElementById('ftp').value
        };
        
        // Don't send masked values
        Object.keys(updates).forEach(key => {
            if (updates[key].startsWith('•')) {
                delete updates[key];
            }
        });
        
        try {
            // Validate first
            const validationResponse = await fetch('/api/settings/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ env: updates })
            });
            
            const validation = await validationResponse.json();
            if (!validation.valid) {
                this.showError(validation.errors.join(', '));
                return;
            }
            
            // Save settings
            const response = await fetch('/api/settings/env', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });
            
            if (response.ok) {
                this.showSuccess('Settings saved successfully');
                this.isDirty = false;
                this.updateSaveButton();
            } else {
                throw new Error('Failed to save settings');
            }
        } catch (error) {
            console.error('Save error:', error);
            this.showError('Failed to save settings');
        }
    }
    
    showSuccess(message) {
        const status = document.getElementById('save-status');
        status.textContent = `✅ ${message}`;
        status.className = 'status-indicator success';
        setTimeout(() => {
            status.textContent = '';
        }, 3000);
    }
    
    showError(message) {
        const status = document.getElementById('save-status');
        status.textContent = `❌ ${message}`;
        status.className = 'status-indicator error';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    new SettingsManager();
});
```

#### Step 3: Create settings.css
```css
/* Settings page styles */
.settings-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Header */
.settings-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    border-bottom: 1px solid #dee2e6;
    background: white;
}

.settings-header h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
}

.close-btn {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #6c757d;
}

/* Main Content */
.settings-content {
    display: flex;
    flex: 1;
    overflow: hidden;
}

/* Navigation */
.settings-nav {
    width: 200px;
    background: #f5f5f5;
    padding: 16px 0;
    overflow-y: auto;
}

.nav-item {
    display: flex;
    align-items: center;
    padding: 12px 24px;
    text-decoration: none;
    color: #212529;
    transition: background 0.2s;
}

.nav-item:hover {
    background: #e3f2fd;
}

.nav-item.active {
    background: #007bff;
    color: white;
}

.nav-item .icon {
    margin-right: 12px;
    font-size: 20px;
}

/* Settings Sections */
.settings-sections {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
    background: white;
}

.settings-section {
    display: none;
    max-width: 800px;
    margin: 0 auto;
}

.settings-section.active {
    display: block;
}

.settings-section h2 {
    font-size: 24px;
    margin-bottom: 24px;
    padding-bottom: 12px;
    border-bottom: 2px solid #e0e0e0;
}

/* Form Groups */
.settings-group {
    margin-bottom: 32px;
}

.settings-group h3 {
    font-size: 18px;
    margin-bottom: 16px;
    color: #495057;
}

.form-group {
    margin-bottom: 16px;
}

.form-group label {
    display: block;
    margin-bottom: 4px;
    font-weight: 500;
    color: #212529;
}

.form-control {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 14px;
}

.form-control:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

/* Input Groups */
.input-group {
    display: flex;
    align-items: center;
}

.input-group .form-control {
    flex: 1;
    border-right: none;
    border-radius: 4px 0 0 4px;
}

.btn-icon {
    padding: 8px 12px;
    background: white;
    border: 1px solid #ced4da;
    border-radius: 0 4px 4px 0;
    cursor: pointer;
}

/* Footer */
.settings-footer {
    display: flex;
    align-items: center;
    padding: 16px 24px;
    border-top: 1px solid #dee2e6;
    background: white;
}

.btn {
    padding: 8px 16px;
    margin-right: 8px;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s;
}

.btn-primary {
    background: #007bff;
    color: white;
}

.btn-primary:hover {
    background: #0056b3;
}

.btn-secondary {
    background: white;
    color: #6c757d;
    border: 1px solid #6c757d;
}

/* Status Indicator */
.status-indicator {
    margin-left: auto;
    font-size: 14px;
}

.status-indicator.success {
    color: #28a745;
}

.status-indicator.error {
    color: #dc3545;
}

/* Responsive */
@media (max-width: 768px) {
    .settings-nav {
        width: 100%;
        display: flex;
        overflow-x: auto;
        padding: 8px;
    }
    
    .settings-content {
        flex-direction: column;
    }
}
```

### 4. Testing Checklist

1. **Unit Tests** (test_settings_service.py):
   - Test env file reading/writing
   - Test API key masking
   - Test validation logic
   - Test backup/restore

2. **Integration Tests**:
   - Test API endpoints
   - Test file permissions
   - Test error handling

3. **Frontend Tests**:
   - Test form validation
   - Test save/load cycle
   - Test error states

### 5. Security Checklist

- [ ] API keys are masked in UI
- [ ] API keys are encrypted in transit (HTTPS)
- [ ] File writes are atomic with backups
- [ ] Input validation prevents injection
- [ ] Sensitive data is not logged
- [ ] CORS is properly configured

### 6. Deployment Steps

1. **Add new dependencies**:
   ```bash
   pip install python-dotenv
   pip freeze > requirements.txt
   ```

2. **Create backup directory**:
   ```bash
   mkdir -p backups/settings
   ```

3. **Update navigation** in index.html:
   ```html
   <a href="/settings" class="settings-link">⚙️ Settings</a>
   ```

4. **Test locally**:
   ```bash
   python web_server.py
   # Navigate to http://localhost:5000/settings
   ```

5. **Deploy**:
   - Ensure backup directory exists on server
   - Test with non-production .env first
   - Monitor logs for any errors

This implementation guide provides a working foundation that can be extended with the additional features outlined in the architecture document.