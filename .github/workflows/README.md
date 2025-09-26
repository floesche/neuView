# GitHub Workflows

This directory contains GitHub Actions workflows for automated testing and continuous integration.

## Workflows

### `test.yml` - Unit Tests
- **Trigger**: Every push and pull request
- **Purpose**: Run unit tests to ensure code quality
- **Environment**: Uses pixi dev environment
- **Commands**: `pixi run test-verbose`

This is the primary workflow that ensures all tests pass on every code change.

### `ci.yml` - Comprehensive CI
- **Trigger**: Push and pull requests to main/develop/master branches
- **Purpose**: Full CI pipeline with tests, coverage, and code quality checks
- **Environment**: Uses pixi dev environment
- **Features**:
  - Unit tests with verbose output
  - Test coverage reporting
  - Code formatting checks with Ruff
  - Code linting with Ruff

## Environment Setup

Both workflows use:
- **pixi**: For dependency management and environment isolation
- **Ubuntu Latest**: As the runner environment
- **Python 3.11+**: Via pixi environment configuration

## Running Tests Locally

To run the same tests locally:

```bash
# Basic tests
pixi run test

# Verbose tests (same as CI)
pixi run test-verbose

# Tests with coverage
pixi run test-coverage

# Code formatting check
pixi run ruff format --check src/ test/

# Code linting
pixi run ruff check src/ test/
```

## Workflow Status

Check the status of workflows:
- View the "Actions" tab in the GitHub repository
- Green checkmarks indicate passing tests
- Red X marks indicate failing tests or issues

## Troubleshooting

If workflows fail:
1. Check the workflow logs in GitHub Actions
2. Run the same commands locally to reproduce issues
3. Ensure all dependencies are properly installed with `pixi install --environment dev`
4. Verify tests pass locally before pushing changes