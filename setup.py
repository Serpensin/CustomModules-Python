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

# Define extras for each module (using lowercase for PyPI compatibility)
extras_require = {
    'apptranslation': read_requirements('AppTranslation'),
    'bitmaphandler': read_requirements('BitmapHandler'),
    'botdirectory': read_requirements('BotDirectory'),
    'databasehandler': read_requirements('DatabaseHandler'),
    'googletrans': read_requirements('Googletrans'),
    'invitetracker': read_requirements('InviteTracker'),
    'killswitch': read_requirements('Killswitch'),
    'libretrans': read_requirements('Libretrans'),
    'loghandler': read_requirements('LogHandler'),
    'patchnotes': read_requirements('Patchnotes'),
    'privatevoice': read_requirements('PrivateVoice'),
    'randomusernames': read_requirements('RandomUsernames'),
    'statdock': read_requirements('StatDock'),
    'steam': read_requirements('Steam'),
    'steamcharts': read_requirements('SteamCharts'),
    'twitch': read_requirements('Twitch'),
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
