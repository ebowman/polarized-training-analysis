# Polarized Training Analysis Documentation

## Overview

This documentation covers the configuration and customization features of the Polarized Training Analysis application, with a focus on the zone distribution system and AI-powered configuration generation.

## Documentation Index

### Core Features

1. **[Settings API Documentation](./SETTINGS_API.md)**
   - Complete API reference for all settings endpoints
   - Environment variable management
   - Prompt template CRUD operations
   - Zone distribution endpoints
   - AI configuration generation endpoints

2. **[Zone Distribution User Guide](./ZONE_DISTRIBUTION_USER_GUIDE.md)**
   - Understanding the 3-zone polarized model
   - Using the visual zone editor
   - Global vs sport-specific settings
   - Monitoring and adjusting distributions

3. **[AI Configuration Generation Guide](./AI_CONFIG_GENERATION_GUIDE.md)**
   - Writing effective workout preferences
   - Using natural language to generate configs
   - Keywords and structure templates
   - Reviewing and adjusting generated configurations

4. **[Zone Distribution Examples](./ZONE_DISTRIBUTION_EXAMPLES.md)**
   - Sport-specific distribution examples
   - Seasonal progression patterns
   - Common mistakes to avoid
   - Best practices for different athlete types

### Integration Guides

5. **[Zone Mapping Guide](./ZONE_MAPPING_GUIDE.md)**
   - Personalized zone calculations
   - Power and heart rate zone mapping
   - Equipment-specific considerations

6. **[Sport Configuration Integration](./SPORT_CONFIG_INTEGRATION.md)**
   - How sport configs work with the system
   - Zone calculation strategies
   - Multi-sport setup

### Technical Documentation

7. **[Zone Breakdown Migration Plan](./ZONE_BREAKDOWN_MIGRATION_PLAN.md)**
   - Technical implementation details
   - Database schema updates
   - Backward compatibility

8. **[AI Preferences to Config Workflow](./AI_PREFERENCES_TO_CONFIG_WORKFLOW.md)**
   - Technical workflow documentation
   - AI prompt engineering
   - Configuration validation

## Quick Start Guides

### Setting Up Zone Distributions

1. Navigate to Settings → Zone Distribution
2. Choose your training philosophy (Polarized/Pyramidal/Threshold)
3. Adjust percentages using sliders or JSON
4. Save changes

### Generating Config from Preferences

1. Write your preferences in natural language
2. Go to Settings → Preferences
3. Click "Generate Configuration"
4. Review and save

### Customizing Sport-Specific Zones

1. Select a sport in Zone Distribution
2. Override global settings
3. Set sport-specific percentages
4. Monitor compliance in analytics

## Feature Highlights

### Zone Distribution Editor
- **Visual sliders** for easy percentage adjustment
- **Preset buttons** for common philosophies
- **Real-time validation** ensuring 100% total
- **Sport-specific overrides** for customization
- **API support** for programmatic updates

### AI Configuration Generator
- **Natural language input** for easy setup
- **Multi-sport detection** from preferences
- **Equipment recognition** (Peloton, Concept2, etc.)
- **Threshold extraction** (FTP, LTHR, pace)
- **Philosophy detection** and zone setup

### Integration Features
- **Personalized zone displays** in the Zone Mapping Guide
- **Automatic zone calculations** based on thresholds
- **Cross-component updates** (changes reflect everywhere)
- **API-first design** for external integrations

## Common Use Cases

### For Cyclists
- Set polarized distribution (80/10/10)
- Configure FTP-based power zones
- Add Peloton-specific workouts
- Track indoor vs outdoor separately

### For Runners
- Use pyramidal approach (70/20/10)
- Configure heart rate zones
- Set threshold pace targets
- Balance easy miles with speedwork

### For Triathletes
- Different distributions per sport
- Swimming: technique-focused
- Cycling: polarized base building
- Running: threshold-focused

### For Coaches
- Set athlete-specific distributions
- Monitor compliance across athletes
- Generate configs from intake forms
- Track seasonal progressions

## API Integration Examples

### Update Zone Distribution
```bash
curl -X PUT http://localhost:5000/api/settings/zone-distribution/sport/Cycling \
  -H "Content-Type: application/json" \
  -d '{"zone_distribution": {"1": 85, "2": 5, "3": 10}}'
```

### Generate Configuration
```bash
curl -X POST http://localhost:5000/api/settings/generate-config \
  -H "Content-Type: application/json" \
  -d '{"preferences": "I am a cyclist with FTP 301W..."}'
```

### Apply Philosophy
```bash
curl -X POST http://localhost:5000/api/settings/zone-distribution/apply-philosophy \
  -H "Content-Type: application/json" \
  -d '{"philosophy": "polarized", "apply_to": "all"}'
```

## Troubleshooting

### Common Issues
- **"Distributions must sum to 100%"**: Check rounding, use normalize button
- **"No AI provider available"**: Configure OpenAI or Claude API keys
- **"Sport not found"**: Check exact spelling in configuration

### Getting Help
1. Check the specific guide for your feature
2. Review API documentation for endpoints
3. Look at examples for your use case
4. Check integration test files for usage patterns

## Version History

### v2.0.0 (Current)
- Added zone distribution editor
- Implemented AI configuration generation
- Enhanced API with batch operations
- Added visual editing interfaces

### v1.0.0
- Initial sport configuration system
- Basic zone calculations
- Manual JSON editing only

## Contributing

When adding new features:
1. Update relevant documentation
2. Add API examples
3. Include in appropriate guides
4. Update this index

## Related Resources

- [Main README](../README.md) - Project overview
- [CLAUDE.md](../CLAUDE.md) - AI assistant instructions
- [Integration Map](../INTEGRATION_MAP.md) - System architecture
- [Settings Implementation Guide](../SETTINGS_IMPLEMENTATION_GUIDE.md) - Development details