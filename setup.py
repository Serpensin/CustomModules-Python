"""Setup configuration for CustomModules package."""
from setuptools import setup, find_packages
import os

# Read the contents of README file
def read_file(filename):
    """Read file contents."""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

# Read dependencies from requirements files
def read_requirements(module_name):
    """Read requirements from module's requirements.txt."""
    req_file = os.path.join(os.path.dirname(__file__), module_name, 'requirements.txt')
    if os.path.exists(req_file):
        with open(req_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Filter out comments and empty lines
            deps = [line.strip() for line in lines 
                   if line.strip() and not line.strip().startswith('#')]
            return deps
    return []

# Define extras for each module
extras_require = {
    'AppTranslation': read_requirements('AppTranslation'),
    'BitmapHandler': read_requirements('BitmapHandler'),
    'BotDirectory': read_requirements('BotDirectory'),
    'DatabaseHandler': read_requirements('DatabaseHandler'),
    'Googletrans': read_requirements('Googletrans'),
    'InviteTracker': read_requirements('InviteTracker'),
    'Killswitch': read_requirements('Killswitch'),
    'Libretrans': read_requirements('Libretrans'),
    'LogHandler': read_requirements('LogHandler'),
    'Patchnotes': read_requirements('Patchnotes'),
    'PrivateVoice': read_requirements('PrivateVoice'),
    'RandomUsernames': read_requirements('RandomUsernames'),
    'StatDock': read_requirements('StatDock'),
    'Steam': read_requirements('Steam'),
    'SteamCharts': read_requirements('SteamCharts'),
    'Twitch': read_requirements('Twitch'),
}

# Create 'all' extra that includes all dependencies
all_deps = set()
for deps in extras_require.values():
    all_deps.update(deps)
extras_require['all'] = sorted(all_deps)

setup(
    name='CustomModules',
    version='1.0.0',
    author='Serpensin',
    description='A collection of custom Python modules for Discord bots and utilities',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/Serpensin/CustomModules-Python',
    packages=find_packages(exclude=['tests', '*.tests', '*.tests.*', 'tests.*']),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Communications :: Chat',
    ],
    python_requires='>=3.10',
    install_requires=[],  # No core dependencies
    extras_require=extras_require,
    license='AGPL-3.0',
    keywords='discord bot utilities modules custom',
    project_urls={
        'Bug Reports': 'https://github.com/Serpensin/CustomModules-Python/issues',
        'Source': 'https://github.com/Serpensin/CustomModules-Python',
    },
)
