# AI Assistant Documentation

This directory contains documentation specifically designed for AI assistants (Claude Code, Cursor, GitHub Copilot, etc.) to understand and work effectively with this codebase.

## Documentation Files

### 📘 PROJECT_CONTEXT.md
**Primary reference for AI assistants**

Comprehensive overview including:
- Project purpose and capabilities
- Technology stack
- Complete project structure
- Core workflows and data flows
- Key components and their responsibilities
- Environment variables
- Development guidelines
- Common tasks
- Data schemas
- Design decisions
- When making changes checklist

**When to read**: First file to read when starting work on any task

### 📋 QUICK_REFERENCE.md
**Quick lookup guide**

Condensed reference including:
- Essential file paths
- Common operations
- File reading priority
- Key configuration
- Data schemas
- Running commands
- Common patterns
- Testing quick reference

**When to read**: When you need quick answers or reminders

## Repository-Wide Documentation

### README.md (root)
Main project README with:
- Project overview and features
- Quick start guide
- Technology stack
- How it works
- Configuration
- Usage examples
- Links to other docs

### ARCHITECTURE.md (root)
System design documentation with:
- Architecture diagrams
- Component descriptions
- Data architecture
- Design patterns
- External dependencies
- Scalability considerations
- Error handling strategy
- Testing strategy

### DEVELOPMENT.md (root)
Developer guide with:
- Prerequisites and setup
- Development workflow
- Code style and standards
- Testing guidelines
- Common development tasks
- Debugging tips
- Troubleshooting

### CONTRIBUTING.md (root)
Contribution guidelines with:
- Code of conduct
- How to contribute
- Development process
- Coding standards
- Commit guidelines
- Pull request process
- Review process

## Other Configuration Files

### .cursorrules (root)
Cursor AI specific rules and context

### .pre-commit-config.yaml (root)
Pre-commit hook configuration

### backend/pyproject.toml
Poetry dependencies and tool configuration

## Recommended Reading Order

### For New AI Assistants
1. `.claude/PROJECT_CONTEXT.md` - Get comprehensive context
2. `ARCHITECTURE.md` - Understand system design
3. `.claude/QUICK_REFERENCE.md` - Bookmark for quick lookups

### For Specific Tasks

#### Adding Features
1. `PROJECT_CONTEXT.md` - Understand existing architecture
2. `ARCHITECTURE.md` - Check design patterns
3. Relevant feature module code
4. `DEVELOPMENT.md` - Follow development workflow

#### Fixing Bugs
1. `QUICK_REFERENCE.md` - Find relevant paths quickly
2. Read the specific file with the bug
3. Check tests to understand expected behavior
4. `DEVELOPMENT.md` - Testing and debugging sections

#### Updating Documentation
1. `CONTRIBUTING.md` - Follow documentation standards
2. Relevant documentation file
3. `PROJECT_CONTEXT.md` - Update if adding new features

#### Code Review
1. `CONTRIBUTING.md` - Review checklist
2. `ARCHITECTURE.md` - Ensure consistency with design
3. `DEVELOPMENT.md` - Verify code standards

## Key Principles for AI Assistants

1. **Always read before editing**
   - Never propose changes without reading the file first
   - Understand context before making modifications

2. **Follow existing patterns**
   - Look at similar code in the codebase
   - Maintain consistency with established patterns

3. **Consult documentation**
   - Check PROJECT_CONTEXT.md for architecture decisions
   - Reference QUICK_REFERENCE.md for common patterns

4. **Test your changes**
   - Add tests for new functionality
   - Run existing tests to ensure nothing breaks

5. **Ask clarifying questions**
   - If requirements are unclear, ask the user
   - Verify assumptions before major changes

6. **Update documentation**
   - Update relevant docs when adding features
   - Keep documentation in sync with code

## Documentation Maintenance

This documentation should be updated when:
- New features are added
- Architecture changes significantly
- New dependencies are introduced
- Development workflow changes
- Common patterns evolve

Maintainers should review and update these files regularly to ensure they remain accurate and helpful for AI assistants.

## Feedback

If you notice documentation gaps or inaccuracies:
1. Create a GitHub issue with the `documentation` label
2. Propose improvements via pull request
3. Discuss in team channels

## Version

Last updated: 2026-06-27
Documentation version: 1.2.0
