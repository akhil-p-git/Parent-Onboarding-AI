#!/bin/bash
# Test runner script for Zapier Triggers API

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
COVERAGE=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -t, --type TYPE    Test type: unit, integration, e2e, load, all (default: all)"
            echo "  -c, --coverage     Enable coverage reporting"
            echo "  -v, --verbose      Verbose output"
            echo "  -h, --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="python -m pytest"

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=backend/app --cov-report=term-missing --cov-report=html"
fi

# Select test directory based on type
case $TEST_TYPE in
    unit)
        echo -e "${YELLOW}Running unit tests...${NC}"
        PYTEST_CMD="$PYTEST_CMD tests/unit -m unit"
        ;;
    integration)
        echo -e "${YELLOW}Running integration tests...${NC}"
        PYTEST_CMD="$PYTEST_CMD tests/integration -m integration"
        ;;
    e2e)
        echo -e "${YELLOW}Running end-to-end tests...${NC}"
        PYTEST_CMD="$PYTEST_CMD -m e2e"
        ;;
    load)
        echo -e "${YELLOW}Running load tests with Locust...${NC}"
        echo "Starting Locust web UI at http://localhost:8089"
        locust -f tests/load/locustfile.py --host=http://localhost:8000
        exit 0
        ;;
    all)
        echo -e "${YELLOW}Running all tests...${NC}"
        PYTEST_CMD="$PYTEST_CMD tests/"
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        exit 1
        ;;
esac

# Run tests
echo -e "${GREEN}Executing: $PYTEST_CMD${NC}"
eval $PYTEST_CMD

# Report result
if [ $? -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
