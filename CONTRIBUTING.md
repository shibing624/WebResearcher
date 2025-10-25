# Contributing to WebResearcher

Thank you for your interest in contributing to WebResearcher! 🎉

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment info (Python version, OS, etc.)

### Suggesting Enhancements

Feature requests are welcome! Please include:
- Use case description
- Proposed solution
- Why this would be valuable

### Pull Requests

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Run tests: `pytest`
5. Commit with clear message: `git commit -m "Add feature X"`
6. Push to your fork: `git push origin feature/your-feature-name`
7. Create a Pull Request

## Development Setup

```bash
# Clone repository
git clone https://github.com/shibing624/WebResearcher.git
cd WebResearcher

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

## Code Style

- Follow PEP 8
- Use type hints
- Add docstrings for public methods
- Keep functions focused and testable

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=webresearcher

# Run specific test
pytest tests/test_react_agent.py
```

## Questions?

Feel free to:
- Open an issue
- Email: xuming624@qq.com
- WeChat: xuming624

We appreciate all contributions! 🙏

