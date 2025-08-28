# Contributing

## Development Setup

```bash
git clone https://github.com/your-username/AWS-observability-platform.git
cd AWS-observability-platform
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install flake8 pytest
```

## Making Changes

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Test: `pytest tests/` and `cdk synth --all`
4. Lint: `flake8 src tests --select=E9,F63,F7,F82`
5. Submit pull request

## Code Standards

- Follow existing code style
- Add tests for new functionality
- Ensure CDK synthesis works
- Keep it simple and functional

## Pull Request Checklist

- [ ] Tests pass locally
- [ ] CDK synthesis succeeds
- [ ] No critical lint errors
- [ ] Clear description of changes