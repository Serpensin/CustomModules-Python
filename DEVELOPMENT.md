# Development Guide

## Local Development and Testing

### Setting Up Local Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/Serpensin/CustomModules-Python.git
   cd CustomModules-Python
   ```

2. Install in development mode:
   ```bash
   pip install -e .
   ```

   Or with specific extras (use lowercase):
   ```bash
   pip install -e .[databasehandler,loghandler]
   ```

   Or with all dependencies:
   ```bash
   pip install -e .[all]
   ```

### Testing Local Changes

After making changes to any module, you can test them immediately since the package is installed in editable mode.

```python
# Test imports
from CustomModules.bitmap_handler import BitmapHandler
from CustomModules.database_handler import DatabaseHandler
from CustomModules.log_handler import LogManager

# Your code here
```

### Building the Package Locally

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Check the built package
twine check dist/*

# Test installation from local build
pip install dist/CustomModules-*.whl
```

### Validating Package Structure

Before committing, run the validation script:

```bash
python validate_structure.py
```

## Adding a New Module

1. Create a new directory for your module:
   ```
   NewModule/
   ├── NewModule.py
   └── requirements.txt
   ```

2. Create a wrapper file in the CustomModules directory:
   ```python
   # CustomModules/new_module.py
   """NewModule module - Description of what it does."""
   import sys
   import os
   
   # Add parent directory to path to allow importing from sibling directories
   _parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   if _parent_dir not in sys.path:
       sys.path.insert(0, _parent_dir)
   
   from NewModule.NewModule import *
   ```

3. Update `CustomModules/__init__.py`:
   - Add the module to the try-except import section
   - Add the module name to `__all__`

4. Update `setup.py`:
   - Add the module to `extras_require` dictionary

5. Update `setup.cfg` (if you're using it):
   - Add the module to `[options.extras_require]`

6. Update the README.md:
   - Add the module to the "Available Modules" section

## Module Structure Best Practices

Each module should:

1. **Have its own directory**: `ModuleName/`
2. **Main Python file**: `ModuleName/ModuleName.py`
3. **Requirements file**: `ModuleName/requirements.txt` (even if empty)
4. **Use snake_case** for the wrapper file: `CustomModules/module_name.py`
5. **Have proper docstrings**: Document what the module does

## Testing Imports

Test that your module can be imported correctly:

```python
# Test basic import
from CustomModules.your_module import YourClass

# Test that dependencies are optional
try:
    from CustomModules.optional_module import OptionalClass
except ImportError:
    print("Optional module not installed - this is expected")
```

## Package Installation Patterns

Users can install your package in several ways:

```bash
# Base package (no dependencies)
pip install CustomModules

# Single module with dependencies
pip install CustomModules[ModuleName]

# Multiple modules
pip install CustomModules[Module1,Module2,Module3]

# All modules and dependencies
pip install CustomModules[all]
```

## Version Bumping

When preparing a new release, update version in three places:

1. `setup.py`: `version='1.0.1'`
2. `pyproject.toml`: `version = "1.0.1"`
3. `CustomModules/__init__.py`: `__version__ = '1.0.1'`

Or use the automated version bumping in the GitHub Actions workflow.

## Pre-Release Checklist

Before publishing a new version:

- [ ] All tests pass locally
- [ ] Version numbers updated in all three files
- [ ] CHANGELOG updated (if you maintain one)
- [ ] README.md is up to date
- [ ] All module requirements.txt files are current
- [ ] Run `python validate_structure.py` successfully
- [ ] Build package locally: `python -m build`
- [ ] Check distribution: `twine check dist/*`
- [ ] Test installation from local build

## Troubleshooting

### Import errors in development

If you get import errors:
```bash
# Reinstall in editable mode
pip uninstall CustomModules
pip install -e .[all]
```

### Module not found

Make sure the module directory exists and contains the .py file:
```bash
ls -la ModuleName/
# Should show ModuleName.py
```

### Dependencies not installing

Check that the module's requirements.txt is properly formatted:
- One dependency per line
- No empty lines at the start
- Comments start with #

## GitHub Actions Workflows

Two workflows are configured:

1. **test-build.yml**: Runs on every push/PR
   - Tests package builds on multiple OS and Python versions
   - Validates imports work correctly

2. **publish-pypi.yml**: Runs on release or manual trigger
   - Builds the package
   - Publishes to PyPI using trusted publishing

## Contributing

When contributing:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Run validation script
6. Submit a pull request

## Support

For questions or issues:
- Open an issue on GitHub
- Check existing documentation
- Review the validation script output
