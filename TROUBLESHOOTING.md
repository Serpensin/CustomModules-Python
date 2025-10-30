# Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### Error: "ModuleNotFoundError: No module named 'CustomModules'"
**Problem:** Package not installed or installed incorrectly.

**Solution:**
```bash
# For development
pip uninstall CustomModules
pip install -e .

# For production
pip install CustomModules
```

#### Error: "No module named 'discord'" or similar dependency errors
**Problem:** Required dependencies for a specific module are not installed.

**Solution:**
Install the package with the appropriate extra for the module you want to use:
```bash
# For a single module (use lowercase)
pip install CustomModules[loghandler]

# For multiple modules
pip install CustomModules[loghandler,databasehandler]

# For all modules
pip install CustomModules[all]
```

### Build Issues

#### Error: "invalid pyproject.toml config"
**Problem:** pyproject.toml has configuration errors.

**Solution:**
- Ensure version format is correct: `version = "2.0.0"`
- Validate SPDX license identifier
- Check that all required fields are present

#### Error: "ModuleNotFoundError: No module named 'discord'"
**Problem:** Module dependencies not installed.

**Solution:**
```bash
# Install with the module's extras
pip install CustomModules[StatDock]

# Or install all dependencies
pip install CustomModules[all]
```

#### Error: "ImportError: cannot import name 'XXX' from 'CustomModules.xxx'"
**Problem:** The module file doesn't export the expected class/function.

**Solution:**
- Check that the original module file exists and contains the class
- Verify the wrapper file imports correctly
- Test direct import: `from ModuleName.ModuleName import XXX`

### Publishing Issues

#### Error: "403 Forbidden" when uploading to PyPI
**Problem:** Invalid credentials or package name already taken.

**Solution:**
```bash
# Check if package name exists
pip search CustomModules

# If name is taken, consider:
# 1. Choose a different name
# 2. Contact PyPI to request ownership
# 3. Add a prefix: CustomModules-YourName
```

#### Error: "400 Bad Request - File already exists"
**Problem:** Version already published to PyPI.

**Solution:**
```bash
# PyPI doesn't allow re-uploading the same version
# Increment version in all three files:
# - setup.py
# - pyproject.toml
# - CustomModules/__init__.py

# Then rebuild:
rm -rf dist build *.egg-info
python -m build
```

#### GitHub Action fails with "No PyPI token"
**Problem:** Using old workflow configuration that requires a token.

**Solution (Trusted Publishing - Recommended):**
1. The current workflow uses Trusted Publishing (no token needed!)
2. Go to https://pypi.org/manage/account/publishing/
3. Add a pending publisher:
   - **PyPI Project Name**: `CustomModules`
   - **Owner**: `Serpensin`
   - **Repository name**: `CustomModules-Python`
   - **Workflow name**: `publish-pypi.yml`
   - **Environment name**: `pypi`
4. Create a release - it will work without any token!

**Alternative Solution (API Token - Legacy):**
1. Go to https://pypi.org → Account Settings → API tokens
2. Create new token (scope: entire account or specific project)
3. Copy the token (starts with `pypi-`)
4. Go to GitHub repository → Settings → Secrets and variables → Actions
5. Create new secret: Name: `PYPI_API_TOKEN`, Value: (paste token)
6. Update workflow to use: `password: ${{ secrets.PYPI_API_TOKEN }}`

### Testing Issues

#### Error: Test imports fail in GitHub Actions
**Problem:** Dependencies not installed in test environment.

**Solution:**
Check `.github/workflows/test-build.yml`:
```yaml
- name: Test install with extras
  run: |
    pip install "dist/*.whl[ModuleName]" || pip install "CustomModules[ModuleName]" -f dist/
```

#### Error: "SyntaxError" in wrapper files
**Problem:** Wrapper file has incorrect import statement.

**Solution:**
Wrapper files should use this pattern:
```python
"""Module description."""
import sys
import os

_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from ModuleName.ModuleName import *
```

### Version Management Issues

#### Error: Versions out of sync
**Problem:** Different versions in different files.

**Solution:**
Always update version in ALL three files:
```python
# setup.py
version='1.0.1'

# pyproject.toml
version = "1.0.1"

# CustomModules/__init__.py
__version__ = '1.0.1'
```

Or use the GitHub Actions workflow which updates them automatically.

### Development Issues

#### Error: Changes not reflected after editing module
**Problem:** Package not installed in editable mode.

**Solution:**
```bash
# Reinstall in editable mode
pip install -e .[all]

# Or if using specific modules
pip install -e .[ModuleName]
```

#### Error: "RuntimeError: No Python environment configured"
**Problem:** VS Code Python environment not selected.

**Solution:**
1. Press Ctrl+Shift+P
2. Type "Python: Select Interpreter"
3. Choose your Python 3.10+ environment
4. Restart terminal

### Dependency Issues

#### Error: "VersionConflict" or dependency resolution fails
**Problem:** Conflicting dependency versions between modules.

**Solution:**
```bash
# Check requirements.txt files for version conflicts
# Update to compatible versions

# Example: If two modules require different discord.py versions
# AppTranslation/requirements.txt: discord.py==2.3.2
# StatDock/requirements.txt: discord.py>=2.3.0

# Use >= instead of == for better compatibility
```

#### Error: "No matching distribution found"
**Problem:** Package name misspelled or doesn't exist.

**Solution:**
```bash
# Check spelling in requirements.txt
# Verify package exists on PyPI
pip search package-name

# Update requirements.txt with correct name
```

### GitHub Actions Issues

#### Workflow doesn't trigger
**Problem:** Workflow triggers not configured correctly.

**Solution:**
Check `.github/workflows/publish-pypi.yml`:
```yaml
on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to publish'
        required: true
```

#### Error: "sed: command not found" on Windows
**Problem:** GitHub Actions uses Linux commands.

**Solution:**
This is normal - the workflow runs on Ubuntu (Linux):
```yaml
jobs:
  build-and-publish:
    runs-on: ubuntu-latest  # Uses Linux
```

### Local Testing Issues

#### Can't test specific module
**Problem:** Module imports fail during testing.

**Solution:**
```bash
# Install in editable mode with specific module
pip install -e .[ModuleName]

# Test import
python -c "from CustomModules.module_name import ClassName"

# If still fails, check:
# 1. Module file exists: ModuleName/ModuleName.py
# 2. Wrapper exists: CustomModules/module_name.py
# 3. requirements.txt exists: ModuleName/requirements.txt
```

### Package Distribution Issues

#### Error: "MANIFEST.in not found" warning
**Problem:** Build system can't find MANIFEST.in.

**Solution:**
MANIFEST.in should be in project root:
```
CustomModules-Python/
├── MANIFEST.in  ← Here
├── setup.py
├── pyproject.toml
└── ...
```

#### Error: Missing files in distribution
**Problem:** Files not included in built package.

**Solution:**
Update `MANIFEST.in`:
```
include README.md
include LICENSE.txt
recursive-include CustomModules *.txt
recursive-include ModuleName *.txt
```

Then rebuild:
```bash
rm -rf dist build *.egg-info
python -m build
```

## Getting Help

If you're still stuck:

1. **Run validation script:**
   ```bash
   python validate_structure.py
   ```

2. **Check build locally:**
   ```bash
   python -m build
   twine check dist/*
   ```

3. **Test installation:**
   ```bash
   pip install dist/*.whl
   python -c "from CustomModules.bitmap_handler import BitmapHandler"
   ```

4. **Check GitHub Actions logs:**
   - Go to repository → Actions
   - Click on failed workflow
   - Read error messages

5. **Search existing issues:**
   - https://github.com/Serpensin/CustomModules-Python/issues

6. **Create new issue:**
   - Include error message
   - Include output of `python validate_structure.py`
   - Include Python version: `python --version`
   - Include pip version: `pip --version`

## Useful Commands

```bash
# Validate package structure
python validate_structure.py

# Clean build artifacts
rm -rf dist build *.egg-info CustomModules.egg-info

# Build package
python -m build

# Check distribution
twine check dist/*

# Install locally in editable mode
pip install -e .[all]

# Test specific import
python -c "from CustomModules.bitmap_handler import BitmapHandler; print('Success!')"

# List installed packages
pip list | grep -i custom

# Uninstall
pip uninstall CustomModules

# Show package info
pip show CustomModules

# Check Python version
python --version

# Check pip version
pip --version

# Upgrade pip
python -m pip install --upgrade pip
```

## Best Practices

1. **Always test locally before publishing:**
   ```bash
   python -m build
   twine check dist/*
   pip install dist/*.whl
   ```

2. **Use virtual environments:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Keep dependencies minimal:**
   - Only include truly required packages in requirements.txt
   - Use extras for optional dependencies

4. **Version consistently:**
   - Update all three version locations
   - Follow semantic versioning (MAJOR.MINOR.PATCH)

5. **Test on multiple Python versions:**
   - GitHub Actions does this automatically
   - Or test locally with different Python versions
