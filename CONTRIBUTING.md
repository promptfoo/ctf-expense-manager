# Contributing to CTF Expense Manager

Thank you for your interest in contributing! This document provides guidelines and instructions for developers.

## Development Setup

### Prerequisites

- Python 3.14
- [uv](https://github.com/astral-sh/uv) (fast Python package installer)

### Getting Started

1. **Clone the repository:**
```bash
git clone <repository-url>
cd ctf-expense-manager
```

2. **Install dependencies:**
```bash
uv sync --extra dev
```

3. **Install pre-commit hooks:**
```bash
uv run pre-commit install
```

## Development Tools

This project uses:
- **uv** for fast, reliable dependency management
- **pytest** for testing with coverage reporting
- **ruff** for linting and code formatting
- **pre-commit** hooks for automated code quality checks
- **GitHub Actions** for continuous integration
- **pyproject.toml** for project configuration

## Quick Commands

Common development tasks:

```bash
# Install dependencies
uv sync --extra dev

# Run tests with coverage
uv run pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Run pre-commit hooks
uv run pre-commit run --all-files

# Start server (requires OPENAI_API_KEY env var)
uv run python -m ctf_expense_manager.server
```

## Code Quality

### Linting

Run the linter to check for code issues:
```bash
uv run ruff check .
```

Auto-fix issues where possible:
```bash
uv run ruff check . --fix
```

### Formatting

Format code according to project standards:
```bash
uv run ruff format .
```

Check if code is formatted correctly:
```bash
uv run ruff format --check .
```

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit. To run them manually on all files:
```bash
uv run pre-commit run --all-files
```

## Testing

### Running Tests

Run the full test suite:
```bash
uv run pytest tests/ -v
```

Run tests with coverage report:
```bash
uv run pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html
```

View HTML coverage report:
```bash
open htmlcov/index.html
```

### Test Requirements

- All new code must have tests
- Maintain minimum 90% test coverage
- All tests must pass before merging

### Test Structure

```
tests/
├── __init__.py
├── test_mock_data.py    # Tests for data layer
├── test_tools.py        # Tests for LangChain tools
└── test_server.py       # Tests for Flask endpoints
```

## Docker

Build and test the Docker image:

```bash
# Build
docker build -t ctf-expense-manager .

# Run
docker run -p 8080:8080 -e OPENAI_API_KEY=your-key ctf-expense-manager

# Test health
curl http://localhost:8080/health
```

## Continuous Integration

The project uses GitHub Actions for CI. On every push and pull request:

### Code Quality (`.github/workflows/ci.yml`)
1. **Linting** - Code must pass ruff checks
2. **Formatting** - Code must be properly formatted
3. **Tests** - All tests must pass with 90%+ coverage on Python 3.14

### Docker (`.github/workflows/docker.yml`)
1. **Build** - Docker image builds successfully
2. **Python version** - Confirms Python 3.14
3. **Dependencies** - All packages import correctly
4. **Health check** - Server starts and responds
5. **Security scan** - Trivy scans for vulnerabilities
6. **Size check** - Warns if image exceeds 500MB (currently ~351MB)

## Pull Request Process

1. **Create a feature branch:**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes and commit:**
```bash
git add .
git commit -m "Description of changes"
```
Pre-commit hooks will run automatically.

3. **Run all checks locally:**
```bash
make check
```

4. **Push your branch:**
```bash
git push origin feature/your-feature-name
```

5. **Create a Pull Request:**
   - Ensure CI checks pass
   - Request review from maintainers
   - Address any feedback

## Project Structure

```
ctf-expense-manager/
├── src/
│   └── ctf_expense_manager/
│       ├── __init__.py        # Package initialization
│       ├── server.py          # Flask app and endpoints
│       ├── tools.py           # LangChain tools for agent
│       └── mock_data.py       # Data layer and models
├── tests/                 # Test suite
├── config.yaml            # CTF platform configuration
├── pyproject.toml         # Project configuration
├── .pre-commit-config.yaml # Pre-commit hooks
└── .github/workflows/     # CI/CD workflows
```

## Code Style

- Follow PEP 8 style guidelines (enforced by ruff)
- Maximum line length: 100 characters
- Use double quotes for strings
- Use type hints where appropriate
- Write clear, descriptive docstrings

## Getting Help

- Check existing issues and pull requests
- Create an issue for bugs or feature requests
- Ask questions in pull request comments

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
