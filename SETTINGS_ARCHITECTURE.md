# Settings Page Architecture Design

## Overview
This document outlines the comprehensive architecture for the Settings page feature in the PolarFlow application. The Settings page will provide a unified interface for managing all application configurations including environment variables, sport configurations, AI provider settings, and prompt templates.

## Core Requirements

### 1. UI Layout and Component Structure

#### Page Layout
```
Settings Page
├── Navigation Header
│   ├── Back to Main Dashboard
│   └── Settings Title
├── Settings Sidebar
│   ├── General Settings
│   ├── Sport Configuration
│   ├── AI Providers
│   ├── Prompt Templates
│   └── Advanced Settings
└── Settings Content Area
    └── Dynamic content based on selected section
```

#### Component Hierarchy
```
SettingsPage
├── SettingsNavigation
│   └── NavigationItem[]
├── SettingsContent
│   ├── GeneralSettings
│   │   ├── StravaConfig
│   │   ├── HeartRateConfig
│   │   └── PowerConfig
│   ├── SportConfiguration
│   │   ├── SportList
│   │   ├── SportEditor
│   │   └── ZoneEditor
│   ├── AIProviderSettings
│   │   ├── ProviderSelector
│   │   ├── APIKeyManager
│   │   └── ProviderTester
│   ├── PromptTemplates
│   │   ├── TemplateList
│   │   ├── TemplateEditor
│   │   └── JSONPreview
│   └── AdvancedSettings
│       ├── EnvironmentEditor
│       └── BackupRestore
└── SettingsFooter
    ├── SaveButton
    ├── CancelButton
    └── StatusIndicator
```

### 2. State Management Architecture

#### Global Settings State
```javascript
const settingsState = {
  // Current view state
  currentSection: 'general',
  isDirty: false,
  isSaving: false,
  
  // Configuration data
  env: {
    strava: {
      clientId: '',
      clientSecret: ''
    },
    training: {
      maxHeartRate: 0,
      ftp: 0,
      averageFtpHr: 0,
      maxFtpHr: 0,
      averageFtpPower: 0
    },
    ai: {
      provider: 'auto',
      primaryProvider: 'openai',
      fallbackProvider: 'claude',
      openaiKey: '',
      anthropicKey: ''
    },
    server: {
      flaskSecretKey: ''
    }
  },
  
  // Sport configuration
  sportConfig: {
    version: '1.0.0',
    userProfile: {},
    sports: [],
    globalSettings: {}
  },
  
  // Prompt templates
  prompts: {
    main: '',
    subPrompts: []
  },
  
  // UI state
  validation: {
    errors: {},
    warnings: {}
  }
}
```

#### State Management Pattern
- Use React Context API for global state
- Local component state for form inputs
- Debounced updates to prevent excessive API calls
- Optimistic updates with rollback on error

### 3. File System Access Strategy

#### Backend API Endpoints
```python
# New endpoints in web_server.py

@app.route('/api/settings/env', methods=['GET', 'POST'])
def handle_env_settings():
    """Get or update .env file contents"""
    
@app.route('/api/settings/sport-config', methods=['GET', 'POST'])
def handle_sport_config():
    """Get or update sport_config.json"""
    
@app.route('/api/settings/prompts', methods=['GET', 'POST'])
def handle_prompt_templates():
    """Get or update prompt templates"""
    
@app.route('/api/settings/validate', methods=['POST'])
def validate_settings():
    """Validate settings before saving"""
    
@app.route('/api/settings/backup', methods=['GET'])
def backup_settings():
    """Create backup of all settings"""
    
@app.route('/api/settings/restore', methods=['POST'])
def restore_settings():
    """Restore settings from backup"""
```

#### File Access Service
```python
class SettingsFileService:
    """Handles secure file system operations for settings"""
    
    def read_env_file(self) -> Dict[str, str]:
        """Read and parse .env file"""
        
    def write_env_file(self, config: Dict[str, str]) -> bool:
        """Safely update .env file with backup"""
        
    def read_sport_config(self) -> TrainingConfig:
        """Read sport configuration"""
        
    def write_sport_config(self, config: TrainingConfig) -> bool:
        """Update sport configuration"""
        
    def create_backup(self) -> str:
        """Create timestamped backup of all settings"""
        
    def restore_backup(self, backup_id: str) -> bool:
        """Restore settings from backup"""
```

### 4. Prompt Template Management System

#### Template Structure
```javascript
const promptTemplate = {
  id: 'main',
  name: 'Main Analysis Prompt',
  description: 'Primary prompt for training analysis',
  version: '1.0.0',
  content: 'Your detailed prompt here...',
  variables: [
    {
      name: 'sport',
      type: 'select',
      options: ['cycling', 'running', 'swimming']
    },
    {
      name: 'volume',
      type: 'number',
      min: 1,
      max: 30
    }
  ],
  subPrompts: [
    {
      id: 'recovery',
      name: 'Recovery Analysis',
      trigger: 'when_recovery_needed',
      content: 'Recovery prompt...'
    }
  ]
}
```

#### Template Editor Features
- Syntax highlighting for prompt content
- Variable insertion with autocomplete
- Real-time preview with sample data
- Template versioning and history
- Import/export functionality

### 5. JSON Generation and Preview

#### JSON Generator Service
```javascript
class JSONGenerator {
  generateSportConfig(formData) {
    // Convert form data to sport_config.json format
  }
  
  generateEnvConfig(formData) {
    // Convert form data to .env format
  }
  
  generatePromptTemplate(formData) {
    // Convert form data to prompt template format
  }
  
  validateJSON(jsonString) {
    // Validate JSON structure
  }
  
  formatJSON(jsonObject) {
    // Pretty format JSON for display
  }
}
```

#### Preview Component
```javascript
const JSONPreview = ({ data, schema }) => {
  // Features:
  // - Syntax highlighted JSON display
  // - Collapsible sections
  // - Diff view for changes
  // - Copy to clipboard
  // - Download as file
  // - Schema validation indicators
}
```

### 6. Data Flow Architecture

#### Read Flow
1. User navigates to Settings page
2. Frontend requests current settings via API
3. Backend reads files (.env, sport_config.json, etc.)
4. Data is parsed and validated
5. Structured data sent to frontend
6. UI components populated with current values

#### Write Flow
1. User modifies settings in UI
2. Local state updated (optimistic update)
3. Validation performed client-side
4. Save request sent to API with changes
5. Backend validates and creates backup
6. Files updated atomically
7. Success/error response to frontend
8. UI updated based on response

#### Validation Flow
1. Real-time validation as user types
2. Debounced API validation for complex rules
3. Cross-field validation (e.g., FTP/HR relationships)
4. Schema validation for JSON structures
5. Clear error messaging and suggestions

## Implementation Details

### Frontend Components (React)

#### SettingsPage.jsx
```javascript
const SettingsPage = () => {
  const [settings, dispatch] = useReducer(settingsReducer, initialState);
  const [activeSection, setActiveSection] = useState('general');
  
  // Load settings on mount
  useEffect(() => {
    loadAllSettings();
  }, []);
  
  // Auto-save with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (settings.isDirty) {
        saveSettings();
      }
    }, 2000);
    return () => clearTimeout(timer);
  }, [settings]);
  
  return (
    <SettingsProvider value={{ settings, dispatch }}>
      <div className="settings-page">
        <SettingsNavigation 
          activeSection={activeSection}
          onSectionChange={setActiveSection}
        />
        <SettingsContent section={activeSection} />
        <SettingsFooter />
      </div>
    </SettingsProvider>
  );
};
```

### Backend Services (Python)

#### settings_service.py
```python
class SettingsService:
    """Centralized service for all settings operations"""
    
    def __init__(self):
        self.file_service = SettingsFileService()
        self.validator = SettingsValidator()
        self.backup_service = BackupService()
        
    def get_all_settings(self) -> Dict[str, Any]:
        """Retrieve all settings from various sources"""
        
    def update_settings(self, section: str, data: Dict) -> bool:
        """Update specific section of settings"""
        
    def validate_settings(self, settings: Dict) -> ValidationResult:
        """Comprehensive validation of all settings"""
        
    def export_settings(self, format: str = 'json') -> str:
        """Export all settings in specified format"""
```

### Security Considerations

1. **API Key Protection**
   - Mask API keys in UI (show only last 4 characters)
   - Encrypt keys in transit
   - Never log or expose keys in errors

2. **File System Security**
   - Validate all file paths
   - Use atomic writes with backups
   - Implement file locking during updates

3. **Input Validation**
   - Sanitize all user inputs
   - Validate against schemas
   - Prevent code injection in formulas

4. **Access Control**
   - Consider adding authentication for settings
   - Log all settings changes
   - Implement rate limiting

## Testing Strategy

### Unit Tests
- Component rendering tests
- State management logic
- File parsing/generation
- Validation rules

### Integration Tests
- API endpoint functionality
- File system operations
- End-to-end user flows

### E2E Tests
- Complete settings update flow
- Backup and restore
- Error handling scenarios

## Migration Plan

1. **Phase 1**: Implement basic settings UI with .env management
2. **Phase 2**: Add sport configuration editor
3. **Phase 3**: Integrate AI provider settings
4. **Phase 4**: Add prompt template management
5. **Phase 5**: Implement advanced features (backup/restore, import/export)

## Future Enhancements

1. **Settings Profiles**
   - Multiple configuration profiles
   - Quick switching between setups
   - Profile sharing/import

2. **Settings Sync**
   - Cloud backup option
   - Multi-device sync
   - Version control integration

3. **Advanced Editors**
   - Visual zone editor with graphs
   - Drag-and-drop workout builder
   - Formula builder UI

4. **Automation**
   - Settings templates for common scenarios
   - Auto-configuration based on athlete data
   - Integration with coaching platforms