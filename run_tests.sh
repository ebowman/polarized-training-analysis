#!/bin/bash
# Test runner script for Polarized Training Analysis

echo "🧪 Running Polarized Training Analysis Tests"
echo "==========================================="

# Run all tests with coverage
echo "Running all tests with coverage..."
pytest --cov=. --cov-report=term-missing

# Generate HTML coverage report
echo -e "\nGenerating HTML coverage report..."
pytest --cov=. --cov-report=html --quiet

echo -e "\n✅ Tests complete! Coverage report available in htmlcov/index.html"

# Run specific test suites
echo -e "\n🎯 Running individual test suites:"
echo -e "\nTraining Analysis Tests:"
pytest tests/test_training_analysis.py -v

echo -e "\nStrava Client Tests:"
pytest tests/test_strava_client.py -v

echo -e "\nWeb Server Tests:"
pytest tests/test_web_server.py -v

echo -e "\nAI Recommendations Tests:"
pytest tests/test_ai_recommendations.py -v