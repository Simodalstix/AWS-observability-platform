# Contributing to AWS Observability Platform

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/AWS-observability-platform.git
   cd AWS-observability-platform
   ```

2. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Code Standards

### Python Code Style
- Follow PEP 8 guidelines
- Use Black for code formatting: `black src tests`
- Use flake8 for linting: `flake8 src tests`
- Use mypy for type checking: `mypy src`

### CDK Best Practices
- Use constructs for reusable components
- Follow AWS CDK best practices
- Include proper resource tagging
- Use least-privilege IAM policies

### Testing Requirements
- Write unit tests for all new functionality
- Maintain test coverage above 80%
- Include integration tests for CDK stacks
- Test with multiple Python versions (3.9, 3.11)

## Submitting Changes

### Pull Request Process
1. Create a feature branch from `main`
2. Make your changes with appropriate tests
3. Ensure all tests pass locally
4. Update documentation if needed
5. Submit a pull request with clear description

### Commit Message Format
```
type(scope): brief description

Detailed explanation of changes if needed.

Fixes #issue-number
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Code Review Checklist
- [ ] Code follows project style guidelines
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] CDK synthesis succeeds
- [ ] Security considerations addressed
- [ ] Performance impact assessed

## Reporting Issues

### Bug Reports
Use the bug report template and include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (AWS region, CDK version, etc.)
- Relevant logs or error messages

### Feature Requests
Use the feature request template and include:
- Problem statement
- Proposed solution
- Implementation considerations
- AWS services involved

## Development Guidelines

### Adding New Stacks
1. Create stack class in `observability/stacks/`
2. Add configuration in `src/config/environment_config.py`
3. Include unit tests in `tests/`
4. Update documentation and README
5. Add to main CDK app

### Adding New Lambda Functions
1. Create function in `src/lambda/`
2. Add construct in `src/constructs/`
3. Include proper error handling and logging
4. Add unit tests and integration tests
5. Document function purpose and usage

### Security Considerations
- Never commit secrets or credentials
- Use IAM roles with least privilege
- Encrypt sensitive data at rest and in transit
- Follow AWS security best practices
- Run security scans before submitting

## Release Process

### Versioning
- Follow Semantic Versioning (SemVer)
- Update CHANGELOG.md with changes
- Tag releases with `v` prefix (e.g., `v1.0.0`)

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in setup.py
- [ ] Security scan clean
- [ ] Performance regression testing

## Getting Help

- **Documentation**: Check the `docs/` directory
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact maintainers for sensitive issues

## Code of Conduct

### Our Standards
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain professional communication

### Enforcement
Violations of the code of conduct should be reported to the project maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.