# Polarized Training Analysis - Test Suite

This directory contains comprehensive tests for the Polarized Training Analysis application.

## Test Structure

- `test_training_analysis.py` - Core training analysis logic tests
- `test_strava_client.py` - Strava API integration tests (mocked)
- `test_web_server.py` - Flask web application tests
- `test_ai_recommendations.py` - AI recommendation engine tests
- `conftest.py` - Shared pytest fixtures

## Running Tests

### Quick Start
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_training_analysis.py

# Run tests matching a pattern
pytest -k "test_from_lthr"

# Run with verbose output
pytest -v
```

### Using the Test Runner Script
```bash
./run_tests.sh
```

### Generate Coverage Report
```bash
# Terminal report
pytest --cov=. --cov-report=term-missing

# HTML report
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Coverage Goals

Current coverage: ~16% (initial test setup)
Target coverage: 80%+

Priority areas for additional tests:
1. Zone calculation edge cases
2. Activity analysis with real Strava data
3. API error handling
4. AI recommendation parsing
5. Download progress tracking

## Writing New Tests

### Example Unit Test
```python
def test_new_feature(self):
    """Test description"""
    # Arrange
    analyzer = TrainingAnalyzer()
    
    # Act
    result = analyzer.new_method()
    
    # Assert
    assert result == expected_value
```

### Example Integration Test
```python
def test_api_endpoint(self, client):
    """Test API endpoint"""
    response = client.get('/api/endpoint')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'expected_key' in data
```

## Mocking External Services

All external services are mocked to ensure tests run without:
- Strava API calls
- OpenAI API calls
- Network requests
- File system dependencies

## CI/CD

Tests run automatically on:
- Push to main branch
- Pull requests
- Can be run manually via GitHub Actions

## Known Issues

1. PowerZones.from_ftp has a bug (0.105 instead of 1.05 for zone4_max)
2. Some methods in ai_recommendations.py need refactoring for better testability
3. Integration tests need better session handling

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Ensure all tests pass
3. Maintain or improve coverage
4. Update this README if needed