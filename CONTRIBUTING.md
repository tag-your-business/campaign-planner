# Contributing to Campaign Planner

Thank you for your interest in contributing to Campaign Planner! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Review Process](#review-process)
- [Community](#community)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors. We expect:

- **Respectful communication**: Be kind and professional
- **Constructive feedback**: Focus on improvement, not criticism
- **Collaboration**: Work together toward shared goals
- **Inclusivity**: Welcome contributors of all skill levels

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks or insults
- Trolling or inflammatory comments
- Sharing private information without permission

## Getting Started

### Prerequisites

Before contributing, ensure you have:

1. **Python 3.13+** installed
2. **Poetry** installed ([installation guide](https://python-poetry.org/docs/#installation))
3. **Git** configured with your name and email
4. An **OpenAI API key** (for testing generation features)

### Setup Your Development Environment

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/campaign-planner.git
   cd campaign-planner
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/campaign-planner.git
   ```

4. **Install dependencies**:
   ```bash
   cd backend
   poetry install --with dev
   ```

5. **Setup pre-commit hooks**:
   ```bash
   poetry run pre-commit install
   ```

6. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

7. **Verify setup**:
   ```bash
   poetry run pytest
   poetry run uvicorn app.main:app --reload
   ```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

#### 🐛 Bug Fixes
- Fix existing bugs
- Improve error handling
- Address edge cases

#### ✨ Features
- Add new functionality
- Enhance existing features
- Improve user experience

#### 📚 Documentation
- Improve README, guides, or API docs
- Add code comments
- Create tutorials or examples

#### 🧪 Tests
- Add unit tests
- Create integration tests
- Improve test coverage

#### 🎨 Code Quality
- Refactor code for clarity
- Optimize performance
- Improve type hints

#### 🔧 Infrastructure
- Improve CI/CD pipelines
- Enhance development tools
- Update dependencies

### Finding Issues to Work On

- **Good First Issues**: Look for issues tagged `good-first-issue`
- **Help Wanted**: Check issues tagged `help-wanted`
- **Feature Requests**: Browse issues tagged `enhancement`
- **Bugs**: Find issues tagged `bug`

If you want to work on something not listed, create an issue first to discuss it.

## Development Process

### 1. Create an Issue (Optional but Recommended)

For significant changes:
1. Search existing issues to avoid duplicates
2. Create a new issue describing:
   - **What** you want to change
   - **Why** it's needed
   - **How** you plan to implement it
3. Wait for maintainer feedback before starting

For small fixes (typos, minor bugs), you can skip this step.

### 2. Create a Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
# OR for bug fixes
git checkout -b fix/issue-description
```

**Branch Naming:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or updates

### 3. Make Your Changes

- Follow the [coding standards](#coding-standards)
- Write tests for new functionality
- Update documentation as needed
- Keep changes focused and atomic

### 4. Test Your Changes

```bash
# Run tests
poetry run pytest

# Run linters
poetry run ruff check .
poetry run black --check .

# Run all pre-commit checks
poetry run pre-commit run --all-files

# Test the application
poetry run uvicorn app.main:app --reload
```

### 5. Commit Your Changes

Follow the [commit guidelines](#commit-guidelines):

```bash
git add .
git commit -m "feat: add campaign approval workflow"
```

### 6. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create PR on GitHub
```

## Coding Standards

### Python Style

We follow **PEP 8** with modifications:

- **Line length**: 100 characters (Black default)
- **Indentation**: 4 spaces
- **Quotes**: Double quotes preferred
- **Imports**: Sorted with `isort`

### Code Formatting

We use **Black** for consistent formatting:

```bash
# Format all files
poetry run black .

# Check formatting
poetry run black --check .
```

Configuration in `pyproject.toml`:
```toml
[tool.black]
line-length = 100
```

### Linting

We use **Ruff** for fast linting:

```bash
# Check for issues
poetry run ruff check .

# Auto-fix issues
poetry run ruff check --fix .
```

### Type Hints

Use type hints where possible:

```python
# Good
def generate_caption(company: str, event: str) -> str:
    return f"{company} - {event}"

# Not ideal (but acceptable for complex cases)
def process_data(data):
    return data
```

### Documentation

#### Docstrings

Use Google-style docstrings:

```python
def create_campaign(company_slug: str, event_name: str) -> Campaign:
    """Create a new campaign for a company event.

    Args:
        company_slug: Unique identifier for the company
        event_name: Name of the event to create campaign for

    Returns:
        Campaign object with generated content

    Raises:
        ValueError: If company_slug is invalid
        OpenAIError: If AI generation fails
    """
    pass
```

#### Comments

- Use comments to explain **why**, not **what**
- Avoid obvious comments
- Keep comments up-to-date with code

```python
# Good: Explains reasoning
# Use exponential backoff to handle API rate limits
retry_delay = 2 ** attempt

# Bad: States the obvious
# Increment counter
counter += 1
```

### File Organization

```python
"""Module description at the top."""

# 1. Standard library imports
import os
from datetime import datetime
from typing import Optional

# 2. Third-party imports
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 3. Local imports
from app.core.config import settings
from app.features.companies.service import CompanyService

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Classes and functions
class CampaignService:
    pass
```

### Testing Standards

#### Test Structure

```python
import pytest
from app.features.generation.caption import generate_caption

def test_generate_caption_success():
    """Test caption generation with valid inputs."""
    # Arrange
    company = "abc_dental"
    event = "World Oral Health Day"

    # Act
    caption = generate_caption(company, event)

    # Assert
    assert isinstance(caption, str)
    assert len(caption) > 0
    assert "dental" in caption.lower()
```

#### Test Coverage

- **Aim for 80%+ coverage** for new features
- **Test edge cases** and error conditions
- **Mock external APIs** (OpenAI, social media)
- **Use fixtures** to reduce duplication

```bash
# Run with coverage
poetry run pytest --cov=app --cov-report=html
```

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, configs)
- `perf`: Performance improvements

### Examples

```bash
# Feature
git commit -m "feat(generation): add support for video content"

# Bug fix
git commit -m "fix(publishing): handle Instagram rate limiting"

# Documentation
git commit -m "docs: update API endpoint examples"

# Multiple paragraphs
git commit -m "feat(scheduler): add configurable retry logic

Schedulers now support exponential backoff and max retry
configuration via environment variables.

Closes #123"
```

### Commit Best Practices

- **Keep commits atomic**: One logical change per commit
- **Write clear subjects**: Describe what the commit does
- **Use imperative mood**: "Add feature" not "Added feature"
- **Reference issues**: Include issue numbers when applicable
- **Explain why**: Use commit body for context

## Pull Request Process

### Before Submitting

Checklist:
- [ ] Code follows style guidelines
- [ ] Tests pass (`poetry run pytest`)
- [ ] Pre-commit hooks pass
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] Branch is up-to-date with main

```bash
# Update your branch
git checkout main
git pull upstream main
git checkout feature/your-feature
git rebase main
```

### PR Title and Description

**Title**: Use conventional commit format
```
feat: add campaign approval workflow
```

**Description**: Include:
1. **What** changed
2. **Why** it was needed
3. **How** it was implemented
4. **Testing** performed
5. **Related issues** (if any)

**Template:**
```markdown
## Description
Brief description of changes

## Motivation
Why this change is needed

## Changes
- Change 1
- Change 2

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing performed

## Screenshots (if applicable)
[Add screenshots]

## Related Issues
Closes #123
```

### PR Size

Keep PRs **focused and manageable**:
- **Small**: < 200 lines (ideal)
- **Medium**: 200-500 lines
- **Large**: > 500 lines (split if possible)

If your PR is large, consider:
- Breaking it into multiple PRs
- Creating a tracking issue
- Discussing the approach first

### Draft PRs

Use draft PRs for:
- Work in progress
- Early feedback
- Architectural discussions

Mark as "Ready for Review" when complete.

## Review Process

### What Reviewers Look For

- **Correctness**: Does it work as intended?
- **Tests**: Are there adequate tests?
- **Code quality**: Is it readable and maintainable?
- **Documentation**: Are changes documented?
- **Performance**: Any performance concerns?
- **Security**: Any security implications?

### Responding to Feedback

- **Be receptive**: Reviews improve code quality
- **Ask questions**: If feedback is unclear
- **Discuss alternatives**: If you disagree
- **Make changes**: Update your PR based on feedback
- **Mark resolved**: After addressing comments

```bash
# Make changes based on feedback
git add .
git commit -m "refactor: address PR feedback"
git push origin feature/your-feature
```

### Merge Requirements

PRs will be merged when:
- [ ] All tests pass
- [ ] At least one approval from maintainer
- [ ] All review comments addressed
- [ ] No merge conflicts
- [ ] CI/CD checks pass

## Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: General questions, ideas
- **Pull Requests**: Code review and discussion

### Getting Help

- **Read the docs**: Check README, DEVELOPMENT.md, ARCHITECTURE.md
- **Search issues**: Your question might be answered
- **Ask in discussions**: For general questions
- **Create an issue**: For bugs or feature requests

### Recognition

Contributors are recognized through:
- Mention in release notes
- Contributor list in repository
- GitHub contributor badges

## Additional Resources

- [Development Guide](DEVELOPMENT.md) - Detailed development setup and workflow
- [Architecture](ARCHITECTURE.md) - System design and component details
- [Project Context](.claude/PROJECT_CONTEXT.md) - Context for AI assistants

## Questions?

If you have questions not covered here:
1. Check existing documentation
2. Search GitHub issues and discussions
3. Create a new discussion or issue

Thank you for contributing to Campaign Planner!
