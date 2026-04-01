.PHONY: help test check fix format lint type coverage clean ci

# Use venv binaries
PYTEST := .venv/bin/pytest
ROFF := .venv/bin/ruff
BLACK := .venv/bin/black
MYPY := .venv/bin/mypy
RADON := .venv/bin/radon
COVERAGE := .venv/bin/coverage

# Default target
help:
	@echo "Available targets:"
	@echo "  make test       - Run tests"
	@echo "  make complexity - Check cyclomatic complexity"
	@echo "  make fix        - Auto-fix lint issues"
	@echo "  make format     - Format code with black"
	@echo "  make lint       - Run ruff linting"
	@echo "  make type       - Run mypy type checking"
	@echo "  make coverage   - Run tests with coverage"
	@echo "  make clean      - Remove coverage and cache files"
	@echo "  make ci         - Full CI pipeline (all checks in order)"

# Run tests
test:
	$(PYTEST) tests/

# Check cyclomatic complexity
complexity:
	$(RADON) cc src/ -a -s

# Auto-fix lint issues
fix:
	$(ROFF) check --fix src/ tests/

# Format code
format:
	$(BLACK) src/ tests/

# Run linting
lint:
	$(ROFF) check src/ tests/

# Type checking
type:
	$(MYPY) src/

# Coverage report
coverage:
	$(COVERAGE) run -m pytest tests/ && $(COVERAGE) report

# Clean cache files
clean:
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov .coverage.*
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Full CI pipeline (in order)
ci: test complexity fix format lint type coverage
	@echo "All checks passed!"
