"""
Test script to validate the CustomModules package structure.
Run this before publishing to ensure everything is set up correctly.
"""
import os
import sys


def check_file_exists(filepath, required=True):
    """Check if a file exists."""
    exists = os.path.exists(filepath)
    status = "✓" if exists else "✗"
    required_text = " (REQUIRED)" if required else " (optional)"
    print(f"{status} {filepath}{required_text if not exists else ''}")
    return exists


def check_directory_exists(dirpath):
    """Check if a directory exists."""
    exists = os.path.isdir(dirpath)
    status = "✓" if exists else "✗"
    print(f"{status} {dirpath}/")
    return exists


def main():
    print("=" * 60)
    print("CustomModules Package Structure Validation")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # Check root files
    print("\n📄 Checking root configuration files...")
    root_files = {
        "setup.py": True,
        "setup.cfg": False,
        "pyproject.toml": True,
        "README.md": True,
        "LICENSE.txt": True,
        "MANIFEST.in": True,
        "PUBLISHING.md": False,
    }
    
    for file, required in root_files.items():
        if not check_file_exists(file, required):
            if required:
                errors.append(f"Missing required file: {file}")
            else:
                warnings.append(f"Missing optional file: {file}")
    
    # Check CustomModules package directory
    print("\n📦 Checking CustomModules package directory...")
    if not check_directory_exists("CustomModules"):
        errors.append("Missing CustomModules package directory!")
        print("\n❌ Cannot continue without CustomModules directory!")
        return False
    
    if not check_file_exists("CustomModules/__init__.py"):
        errors.append("Missing CustomModules/__init__.py!")
    
    # Check module wrapper files
    print("\n🔧 Checking module wrapper files...")
    modules = [
        "app_translation",
        "bitmap_handler",
        "bot_directory",
        "database_handler",
        "googletrans",
        "invite_tracker",
        "killswitch",
        "libretrans",
        "log_handler",
        "patchnotes",
        "private_voice",
        "random_usernames",
        "stat_dock",
        "steam",
        "steam_charts",
        "twitch",
    ]
    
    for module in modules:
        if not check_file_exists(f"CustomModules/{module}.py"):
            errors.append(f"Missing wrapper file: CustomModules/{module}.py")
    
    # Check original module directories
    print("\n📁 Checking original module directories...")
    original_modules = {
        "AppTranslation": "AppTranslation.py",
        "BitmapHandler": "BitmapHandler.py",
        "BotDirectory": "BotDirectory.py",
        "DatabaseHandler": "DatabaseHandler.py",
        "Googletrans": "Googletrans.py",
        "InviteTracker": "InviteTracker.py",
        "Killswitch": "Killswitch.py",
        "Libretrans": "Libretrans.py",
        "LogHandler": "LogHandler.py",
        "Patchnotes": "Patchnotes.py",
        "PrivateVoice": "PrivateVoice.py",
        "RandomUsernames": "RandomUsernames.py",
        "StatDock": "StatDock.py",
        "Steam": "Steam.py",
        "SteamCharts": "SteamCharts.py",
        "Twitch": "Twitch.py",
    }
    
    for module_dir, module_file in original_modules.items():
        dir_exists = check_directory_exists(module_dir)
        if dir_exists:
            file_path = os.path.join(module_dir, module_file)
            if not check_file_exists(file_path):
                errors.append(f"Missing module file: {file_path}")
        else:
            errors.append(f"Missing module directory: {module_dir}/")
    
    # Check GitHub workflows
    print("\n⚙️ Checking GitHub workflows...")
    check_file_exists(".github/workflows/publish-pypi.yml", required=True)
    check_file_exists(".github/workflows/test-build.yml", required=False)
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    if errors:
        print(f"\n❌ Found {len(errors)} error(s):")
        for error in errors:
            print(f"  • {error}")
    
    if warnings:
        print(f"\n⚠️ Found {len(warnings)} warning(s):")
        for warning in warnings:
            print(f"  • {warning}")
    
    if not errors and not warnings:
        print("\n✅ All checks passed! Package structure is valid.")
        print("\n📦 Next steps:")
        print("  1. Update version numbers in setup.py, pyproject.toml, and CustomModules/__init__.py")
        print("  2. Commit and push your changes")
        print("  3. Create a GitHub release or run the workflow manually")
        print("  4. Package will be automatically published to PyPI")
        return True
    elif not errors:
        print("\n✅ All required checks passed!")
        print("⚠️ Some optional files are missing, but you can proceed.")
        return True
    else:
        print("\n❌ Please fix the errors before publishing!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
