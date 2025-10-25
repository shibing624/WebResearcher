# Release Guide for WebResearcher

This document describes the process for releasing new versions of WebResearcher to PyPI.

## Prerequisites

1. Install required tools:
   ```bash
   pip install build twine
   ```

2. Ensure you have PyPI credentials configured:
   ```bash
   # Create ~/.pypirc
   [distutils]
   index-servers =
       pypi
   
   [pypi]
   username = __token__
   password = pypi-YOURTOKENHERE
   ```

## Release Process

### 1. Update Version

Edit `webresearcher/__init__.py`:
```python
__version__ = "0.1.1"  # Bump version
```

### 2. Update CHANGELOG.md

Add new version section with changes:
```markdown
## [0.1.1] - 2025-XX-XX

### Added
- New feature X
- New feature Y

### Fixed
- Bug fix Z
```

### 3. Commit Changes

```bash
git add webresearcher/__init__.py CHANGELOG.md
git commit -m "Bump version to 0.1.1"
git tag v0.1.1
git push && git push --tags
```

### 4. Build Package

```bash
# Clean old builds
rm -rf build/ dist/ *.egg-info

# Build new distribution
python -m build
```

This creates:
- `dist/webresearcher-X.Y.Z-py3-none-any.whl` (wheel)
- `dist/webresearcher-X.Y.Z.tar.gz` (source distribution)

### 5. Check Package

```bash
# Validate package
python -m twine check dist/*
```

Should output:
```
Checking dist/webresearcher-X.Y.Z-py3-none-any.whl: PASSED
Checking dist/webresearcher-X.Y.Z.tar.gz: PASSED
```

### 6. Test Upload (TestPyPI)

```bash
# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ webresearcher
```

### 7. Upload to PyPI

```bash
# Upload to real PyPI
python -m twine upload dist/*
```

### 8. Verify Installation

```bash
# Create fresh virtual environment
python -m venv test_env
source test_env/bin/activate

# Install from PyPI
pip install webresearcher

# Test it works
webresearcher "Test question" --help
python -c "from webresearcher import MultiTurnReactAgent; print('OK')"

# Cleanup
deactivate
rm -rf test_env
```

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (X.0.0): Incompatible API changes
- **MINOR** version (0.X.0): New features, backward compatible
- **PATCH** version (0.0.X): Bug fixes, backward compatible

Examples:
- `0.1.0` → `0.1.1`: Bug fix
- `0.1.1` → `0.2.0`: New feature
- `0.9.0` → `1.0.0`: Stable release with breaking changes

## Checklist

Before releasing:

- [ ] Version bumped in `__init__.py`
- [ ] CHANGELOG.md updated
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Package builds successfully
- [ ] Package validated with twine
- [ ] Tested on TestPyPI
- [ ] Git tagged with version
- [ ] Changes pushed to GitHub
- [ ] Package uploaded to PyPI
- [ ] Installation verified

## Post-Release

- Announce on GitHub Releases
- Update documentation
- Share on social media (optional)

## Questions?

Contact: xuming624@qq.com

