# Testing Infrastructure Setup Guide

## Overview

This guide provides instructions for using the pytest test suite and continuous integration configuration for the Anomaly Checker project. The testing infrastructure ensures code quality, prevents regressions, and validates theoretical predictions across different computing environments.

## Local Development Setup

### Prerequisites

Ensure Python 3.8 or higher is installed on your system. The anomaly checker uses only standard library modules for core functionality, but the testing infrastructure requires additional packages.

### Installation

Clone the repository and install the testing dependencies:

```bash
git clone [repository-url]
cd anomaly-checker
pip install -r requirements.txt
```

### Directory Structure

Organize your project files as follows:

```
anomaly-checker/
├── anomaly_checker.py          # Main implementation (v0.1)
├── test_anomaly_checker.py     # Pytest test suite
├── requirements.txt            # Python dependencies
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions configuration
└── README.md                   # This guide
```

## Running Tests Locally

### Basic Test Execution

Run all tests with verbose output:

```bash
pytest test_anomaly_checker.py -v
```

### Test Coverage Analysis

Generate a coverage report to identify untested code paths:

```bash
pytest test_anomaly_checker.py --cov=anomaly_checker --cov-report=html
open htmlcov/index.html  # View detailed coverage report
```

### Running Specific Test Classes

Test only Standard Model verification:

```bash
pytest test_anomaly_checker.py::TestStandardModelAnomaly -v
```

Test only BSM scenarios:

```bash
pytest test_anomaly_checker.py::TestBSMModels -v
```

### Performance Testing

Run benchmarks to ensure computational efficiency:

```bash
pytest test_anomaly_checker.py -v --benchmark-only
```

## Continuous Integration

The GitHub Actions workflow automatically runs on every push and pull request. The CI pipeline performs the following checks:

### Multi-Platform Testing

Tests run on Ubuntu, macOS, and Windows with Python versions 3.8 through 3.12, ensuring broad compatibility.

### Code Quality Checks

The pipeline includes automated linting with flake8 and type checking with mypy. These tools catch common errors and enforce consistent code style.

### Integration Testing

The CI verifies that JSON model loading works correctly and that command-line interfaces function as expected.

### Performance Benchmarking

Automated benchmarks track computational performance to prevent efficiency regressions as the codebase grows.

## Adding New Tests

### Test Structure

Each test should follow the arrange-act-assert pattern:

```python
def test_new_anomaly_scenario(self):
    # Arrange: Set up test data
    fermions = create_test_spectrum()
    
    # Act: Perform the calculation
    checker = AnomalyChecker(fermions)
    result = checker.verify_cancellation()
    
    # Assert: Verify expectations
    assert result[0] is True, "Anomalies should cancel"
```

### Testing New Models

When implementing a new BSM scenario, add a test to verify anomaly cancellation:

```python
def test_custom_bsm_model(self):
    """Test anomaly cancellation for [model name]"""
    fermions = standard_model_spectrum(False)
    
    # Add BSM content
    fermions.extend([
        # Define new fermions here
    ])
    
    checker = AnomalyChecker(fermions)
    all_cancel, failures = checker.verify_cancellation()
    
    assert all_cancel is True, f"Anomalies found: {failures}"
```

### Edge Case Testing

Include tests for boundary conditions and error cases to ensure robust error handling throughout the codebase.

## Troubleshooting

### Common Issues

If tests fail due to import errors, ensure the anomaly_checker.py file is in the same directory as the test file.

If numerical precision issues arise, verify that all calculations use fractions.Fraction for exact arithmetic rather than floating-point approximations.

### CI Failures

Check the GitHub Actions log for detailed error messages. The most common issues involve platform-specific path handling or Python version incompatibilities.

## Best Practices

Maintain test independence by avoiding shared state between tests. Each test should create its own fermion spectrum and checker instance.

Use descriptive test names that clearly indicate what aspect of the code is being verified. This aids in debugging when tests fail.

Keep tests focused on single aspects of functionality. Complex tests that verify multiple behaviors simultaneously are harder to debug and maintain.

Document any non-obvious test logic with comments explaining the theoretical motivation or the specific edge case being tested.

## Next Steps

With the testing infrastructure in place, the team can confidently explore new theoretical models while maintaining code quality. The automated CI pipeline ensures that all contributions meet quality standards before merging.

For questions about specific test implementations or CI configuration, consult the inline documentation in the test files or reach out to the development team.