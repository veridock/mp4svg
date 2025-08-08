# Makefile for MP4SVG project
# Supports development, testing, building, publishing, and Docker operations

.PHONY: help install install-dev test test-coverage lint format type-check \
        build publish publish-test clean docs docker-build docker-run \
        docker-push shell api server all

# Variables
PACKAGE_NAME = mp4svg
PYTHON = python3
PIP = pip3
POETRY = poetry
DOCKER_IMAGE = mp4svg
DOCKER_TAG = latest

# Default target
help: ## Show this help message
	@echo "MP4SVG Project - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick start:"
	@echo "  make install-dev  # Install development dependencies"
	@echo "  make test         # Run tests"
	@echo "  make build        # Build package"
	@echo "  make docker-build # Build Docker image"

# Installation targets
install: ## Install package for production
	$(PIP) install .

install-dev: ## Install package with development dependencies
	$(POETRY) install --with dev
	$(PIP) install -e .

install-deps: ## Install system dependencies (Ubuntu/Debian)
	sudo apt-get update
	sudo apt-get install -y python3-dev python3-pip python3-venv
	sudo apt-get install -y libopencv-dev python3-opencv
	sudo apt-get install -y build-essential

# Development targets
test: ## Run tests
	$(POETRY) run pytest tests/ -v

test-coverage: ## Run tests with coverage report
	$(POETRY) run pytest tests/ -v --cov=src/$(PACKAGE_NAME) --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode
	$(POETRY) run pytest-watch tests/

lint: ## Run linting (flake8, black check)
	$(POETRY) run flake8 src/ tests/
	$(POETRY) run black --check src/ tests/

format: ## Format code with black and isort
	$(POETRY) run black src/ tests/
	$(POETRY) run isort src/ tests/

type-check: ## Run type checking with mypy
	$(POETRY) run mypy src/$(PACKAGE_NAME)

check-all: lint type-check test ## Run all code quality checks

# Build targets
build: clean ## Build package
	$(POETRY) version patch
	$(POETRY) build

build-wheel: clean ## Build wheel only
	$(POETRY) build --format wheel

build-sdist: clean ## Build source distribution only
	$(POETRY) build --format sdist

# Publishing targets
publish: build ## Publish to PyPI
	@echo "Publishing to PyPI..."
	$(POETRY) publish

publish-test: build ## Publish to TestPyPI
	@echo "Publishing to TestPyPI..."
	$(POETRY) config repositories.testpypi https://test.pypi.org/legacy/
	$(POETRY) publish --repository testpypi

check-publish: ## Check if package can be published
	$(POETRY) check
	$(POETRY) build --dry-run

# Documentation targets
docs: ## Generate documentation
	@echo "Generating documentation..."
	mkdir -p docs
	$(POETRY) run pydoc-markdown -I src/ -m $(PACKAGE_NAME) --render-toc > docs/api.md

docs-serve: ## Serve documentation locally
	@echo "Starting documentation server..."
	cd docs && $(PYTHON) -m http.server 8080

# Docker targets
docker-build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-build-dev: ## Build Docker image for development
	@echo "Building development Docker image..."
	docker build -f Dockerfile.dev -t $(DOCKER_IMAGE):dev .

docker-run: ## Run Docker container interactively
	@echo "Running Docker container..."
	docker run -it --rm \
		-v $(PWD)/data:/app/data \
		-p 8000:8000 \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

docker-shell: ## Start Docker container with shell
	docker run -it --rm \
		-v $(PWD):/app \
		$(DOCKER_IMAGE):$(DOCKER_TAG) \
		/bin/bash

docker-api: ## Run API server in Docker
	docker run -d --name $(PACKAGE_NAME)-api \
		-p 8000:8000 \
		-v $(PWD)/data:/app/data \
		$(DOCKER_IMAGE):$(DOCKER_TAG) \
		mp4svg-api

docker-stop: ## Stop Docker containers
	docker stop $(PACKAGE_NAME)-api || true
	docker rm $(PACKAGE_NAME)-api || true

docker-push: docker-build ## Push Docker image to registry
	@echo "Pushing Docker image..."
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	docker push $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)

docker-clean: ## Clean Docker images and containers
	docker system prune -f
	docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) || true
	docker rmi $(DOCKER_IMAGE):dev || true

# Application runners
shell: install-dev ## Start interactive shell
	$(POETRY) run mp4svg-shell

api: install-dev ## Start API server
	$(POETRY) run mp4svg-api

server: api ## Alias for api

# Demo and examples
demo: install-dev ## Run demo conversion
	@echo "Running demo conversion..."
	@if [ ! -f demo/input.mp4 ]; then \
		echo "Creating demo directory and sample file..."; \
		mkdir -p demo; \
		echo "Please place a test MP4 file at demo/input.mp4"; \
		exit 1; \
	fi
	$(POETRY) run mp4svg demo/input.mp4 demo/output.svg --method ascii85
	@echo "Demo completed! Check demo/output.svg"

benchmark: install-dev ## Run performance benchmark
	@echo "Running performance benchmark..."
	mkdir -p benchmark
	$(POETRY) run python scripts/benchmark.py

# Validation and testing
validate-install: ## Validate installation
	@echo "Validating installation..."
	$(PYTHON) -c "import $(PACKAGE_NAME); print(f'$(PACKAGE_NAME) version: {$(PACKAGE_NAME).__version__}')"
	$(PYTHON) -c "from $(PACKAGE_NAME) import ASCII85SVGConverter; print('ASCII85 converter: OK')"
	$(PYTHON) -c "from $(PACKAGE_NAME).validators import SVGValidator; print('SVG validator: OK')"

test-install: build ## Test installation from built package
	$(PIP) install dist/*.whl --force-reinstall
	$(MAKE) validate-install

integration-test: ## Run integration tests
	@echo "Running integration tests..."
	$(POETRY) run pytest tests/test_integration.py -v

performance-test: ## Run performance tests
	@echo "Running performance tests..."
	$(POETRY) run pytest tests/test_performance.py -v

# Cleanup targets
clean: ## Clean build artifacts
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .tox/
	find . -type d -name __pycache__ -not -path "./venv/*" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -not -path "./venv/*" -not -path "./.venv/*" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -not -path "./venv/*" -not -path "./.venv/*" -delete 2>/dev/null || true

clean-all: clean docker-clean ## Clean everything including Docker

# Release management
bump-patch: ## Bump patch version
	$(POETRY) version patch
	@echo "Version bumped to: $$($(POETRY) version -s)"

bump-minor: ## Bump minor version
	$(POETRY) version minor
	@echo "Version bumped to: $$($(POETRY) version -s)"

bump-major: ## Bump major version
	$(POETRY) version major
	@echo "Version bumped to: $$($(POETRY) version -s)"

release-patch: bump-patch build publish ## Release patch version
	@echo "Patch release completed!"

release-minor: bump-minor build publish ## Release minor version
	@echo "Minor release completed!"

release-major: bump-major build publish ## Release major version
	@echo "Major release completed!"

# Git helpers
git-tag: ## Create git tag for current version
	@VERSION=$$($(POETRY) version -s); \
	echo "Creating tag v$$VERSION"; \
	git tag -a v$$VERSION -m "Release v$$VERSION"; \
	git push origin v$$VERSION

git-clean: ## Clean git repository
	git clean -fdx

# Security and quality
security-scan: ## Run security scan with bandit
	$(POETRY) run bandit -r src/

dependency-check: ## Check for dependency vulnerabilities
	$(POETRY) run safety check

audit: security-scan dependency-check ## Run all security audits

# Development utilities
init: ## Initialize development environment
	@echo "Initializing development environment..."
	$(MAKE) install-dev
	$(MAKE) validate-install
	@echo "Development environment ready!"

update-deps: ## Update all dependencies
	$(POETRY) update

lock-deps: ## Lock dependency versions
	$(POETRY) lock

requirements: ## Generate requirements.txt
	$(POETRY) export -f requirements.txt --output requirements.txt
	$(POETRY) export -f requirements.txt --dev --output requirements-dev.txt

# CI/CD helpers
ci-test: ## Run CI tests (used by GitHub Actions)
	$(MAKE) install-dev
	$(MAKE) lint
	$(MAKE) type-check  
	$(MAKE) test-coverage
	$(MAKE) build
	$(MAKE) test-install

ci-publish: ## Publish from CI (requires tokens)
	$(MAKE) check-publish
	$(MAKE) publish

# All-in-one targets
all: clean install-dev check-all build ## Run complete build pipeline

dev: install-dev ## Setup for development
	@echo "Development setup complete!"
	@echo "Available commands:"
	@echo "  make shell  - Start interactive shell"
	@echo "  make api    - Start API server"
	@echo "  make test   - Run tests"

# Version information
version: ## Show current version
	@echo "Package version: $$($(POETRY) version -s)"
	@echo "Git commit: $$(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"
	@echo "Python version: $$($(PYTHON) --version)"

# Quick help for common tasks
.PHONY: quick-help
quick-help: ## Show quick help for common tasks
	@echo "🚀 Quick Start Guide:"
	@echo ""
	@echo "Development setup:"
	@echo "  make init        # Setup development environment"
	@echo "  make demo        # Run demo conversion"
	@echo ""
	@echo "Testing:"
	@echo "  make test        # Run all tests"  
	@echo "  make lint        # Check code style"
	@echo "  make format      # Format code"
	@echo ""
	@echo "Building:"
	@echo "  make build       # Build package"
	@echo "  make docker-build # Build Docker image"
	@echo ""
	@echo "Running:"
	@echo "  make shell       # Interactive CLI"
	@echo "  make api         # Start API server"
	@echo ""
	@echo "Publishing:"
	@echo "  make publish-test # Publish to TestPyPI"
	@echo "  make publish     # Publish to PyPI"
