# QA Settings Page Test Checklist

## Test Date: 2025-01-17
## Tester: QA Validator Agent

### Issues Found

#### 1. FTP Label Issue ❌
- **Expected**: "Functional Threshold Power (FTP)"
- **Actual**: Settings page shows "FTP Configuration" section with FTP host/username/password fields
- **Status**: FAILED - This appears to be File Transfer Protocol settings, not Functional Threshold Power

#### 2. Gemini in AI Provider Dropdown ❌
- **Expected**: Gemini should be removed from dropdown
- **Actual**: Line 321 in settings.html still includes `<option value="gemini">Gemini (Google)</option>`
- **Status**: FAILED - Gemini is still present in the dropdown

#### 3. API Provider Preference Options ❓
- **Expected**: "Prefer OpenAI" and "Prefer Claude" options
- **Actual**: Dropdown shows individual providers (OpenAI, Claude, Gemini, Local Model) but no preference options
- **Status**: NEEDS CLARIFICATION - The current implementation uses single provider selection, not preference-based fallback

### Test Scenarios

#### Scenario 1: Only OpenAI Key Present
- **Test**: Remove Claude key, keep only OpenAI key
- **Expected**: System should work with OpenAI only
- **Status**: NOT TESTED - Need to verify backend handles missing keys gracefully

#### Scenario 2: Only Claude Key Present  
- **Test**: Remove OpenAI key, keep only Claude key
- **Expected**: System should work with Claude only
- **Status**: NOT TESTED - Need to verify backend handles missing keys gracefully

#### Scenario 3: No API Keys Present
- **Test**: Remove all API keys
- **Expected**: System should show appropriate error message
- **Status**: NOT TESTED - Need to verify error handling

### Additional Findings

1. **Navigation**: Settings page is accessible at `/settings` route
2. **API Endpoints**: 
   - GET/POST `/api/settings` endpoints exist in web_server.py
   - Additional endpoints for env, sport-config, prompts are defined
3. **UI Structure**: Settings page has tabs for Environment, AI Prompts, Sport Configuration, and Preview
4. **Security**: API keys are properly masked in the preview tab

### Recommendations

1. **URGENT**: Fix the FTP section - it should be for "Functional Threshold Power" athletic metric, not File Transfer Protocol
2. **URGENT**: Remove Gemini from the AI provider dropdown as requested
3. **CLARIFICATION NEEDED**: The current design uses single provider selection. Should we implement a preference-based system with fallback logic instead?
4. **TESTING**: Need to run live tests for error handling scenarios

### Next Steps

1. Report these findings to the implementation team
2. Wait for fixes to be implemented
3. Re-test after fixes are applied
4. Perform live testing of error handling scenarios