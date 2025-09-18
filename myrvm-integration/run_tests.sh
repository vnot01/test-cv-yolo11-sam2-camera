#!/bin/bash
# Integration Test Runner Script
# Run this script to test the MyRVM integration

echo "🚀 MyRVM Integration Test Runner"
echo "================================"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Please activate your virtual environment first:"
    echo "  source ../myenv/bin/activate"
    exit 1
fi

echo "✅ Virtual environment: $VIRTUAL_ENV"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✅ Python version: $python_version"

# Check if we're in the right directory
if [[ ! -f "debug/test_integration.py" ]]; then
    echo "❌ Please run this script from the myrvm-integration directory"
    exit 1
fi

echo "✅ Running from correct directory"

# Create logs directory if it doesn't exist
mkdir -p logs

# Run integration tests
echo ""
echo "🧪 Running Integration Tests..."
echo "================================"

python3 debug/test_integration.py

# Check exit code
if [[ $? -eq 0 ]]; then
    echo ""
    echo "🎉 All tests passed!"
    echo "✅ Integration is ready"
else
    echo ""
    echo "❌ Some tests failed!"
    echo "Please check the logs for details"
    exit 1
fi

echo ""
echo "📊 Test Results Summary:"
echo "========================"
echo "Check logs/integration_test_results_*.json for detailed results"
echo "Check logs/*.log for detailed logs"

echo ""
echo "🚀 Next Steps:"
echo "=============="
echo "1. Review test results in logs/"
echo "2. Fix any failed tests"
echo "3. Run: python3 main/jetson_main.py"
echo "4. Monitor with: python3 debug/system_monitor.py"
