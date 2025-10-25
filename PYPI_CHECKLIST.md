# PyPI Publication Checklist

Use this checklist before publishing WebResearcher to PyPI.

## ✅ Pre-Release Checklist

### Code Quality
- [x] All tests passing (`pytest`)
- [x] No linting errors
- [x] Type hints complete
- [x] Documentation up to date
- [x] Examples working
- [x] CHANGELOG.md updated

### Package Files
- [x] `setup.py` configured correctly
- [x] `pyproject.toml` configured correctly
- [x] `__init__.py` with `__version__`
- [x] `README.md` comprehensive
- [x] `README_zh.md` available
- [x] `LICENSE` file present
- [x] `MANIFEST.in` complete
- [x] `.gitignore` configured

### Dependencies
- [x] `requirements.txt` accurate
- [x] No unnecessary dependencies
- [x] Version constraints appropriate
- [x] All imports work

### Build Process
- [x] Clean build (`rm -rf build dist *.egg-info`)
- [x] Build successful (`python -m build`)
- [x] Twine check passes (`twine check dist/*`)
- [x] Package size reasonable (<100KB)

## 📋 Publication Steps

### Step 1: Final Verification

```bash
# 1. Clean previous builds
rm -rf build/ dist/ *.egg-info

# 2. Build new package
python -m build

# 3. Check package
python -m twine check dist/*

# 4. Expected output:
#    Checking dist/webresearcher-X.Y.Z-py3-none-any.whl: PASSED
#    Checking dist/webresearcher-X.Y.Z.tar.gz: PASSED
```

### Step 2: Test on TestPyPI

```bash
# 1. Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# 2. Create test virtualenv
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# 3. Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple webresearcher

# 4. Test installation
webresearcher --version
webresearcher --help
python -c "from webresearcher import MultiTurnReactAgent; print('✅ Import OK')"

# 5. Cleanup
deactivate
rm -rf test_env
```

### Step 3: Publish to PyPI

```bash
# 1. Upload to PyPI (PRODUCTION)
python -m twine upload dist/*

# You'll be prompted for:
#   - Username: __token__
#   - Password: pypi-AgEIcHl... (your PyPI token)

# 2. Verify on PyPI
#    Visit: https://pypi.org/project/webresearcher/
```

### Step 4: Post-Publication

```bash
# 1. Test installation
pip install webresearcher

# 2. Verify functionality
webresearcher --version
webresearcher "Test question" --help

# 3. Create GitHub Release
#    - Go to: https://github.com/shibing624/WebResearcher/releases
#    - Click "Create a new release"
#    - Tag: v0.1.0
#    - Title: WebResearcher v0.1.0
#    - Description: Copy from CHANGELOG.md
#    - Attach: dist/webresearcher-0.1.0.tar.gz

# 4. Announce
#    - Update project homepage
#    - Social media (optional)
#    - Notify users
```

## 🔐 PyPI Token Setup

### First Time Setup

1. Go to https://pypi.org/manage/account/token/
2. Create a new API token
3. Scope: "Entire account" or "Project: webresearcher"
4. Copy the token (starts with `pypi-`)

### Configure Twine

Option 1: Using `.pypirc` file

```bash
# Create ~/.pypirc
cat > ~/.pypirc <<EOF
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE

[testpypi]
username = __token__
password = pypi-YOUR-TEST-TOKEN-HERE
EOF

# Secure the file
chmod 600 ~/.pypirc
```

Option 2: Using environment variables

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR-TOKEN-HERE
```

## 🐛 Troubleshooting

### Build fails

```bash
# Update build tools
pip install --upgrade build setuptools wheel

# Try building again
python -m build
```

### Upload fails

```bash
# Check package first
twine check dist/*

# Ensure you're using token authentication
# Username should be: __token__
# Password should be: pypi-...
```

### Import errors after installation

```bash
# Check what was installed
pip show webresearcher
pip show -f webresearcher

# Try reinstalling
pip uninstall webresearcher
pip install webresearcher
```

## ✅ Final Checklist

Before clicking "Upload":

- [ ] Version bumped correctly
- [ ] CHANGELOG updated
- [ ] README accurate
- [ ] Tests pass
- [ ] Build successful
- [ ] Twine check passed
- [ ] Tested on TestPyPI
- [ ] Git tag created
- [ ] Changes pushed to GitHub

## 📞 Help

If you encounter issues:

1. Check [RELEASE.md](./RELEASE.md) for detailed release guide
2. Open an issue: https://github.com/shibing624/WebResearcher/issues
3. Email: xuming624@qq.com

---

Good luck with your PyPI publication! 🚀

