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

# Define extras for each module (using lowercase for PyPI compatibility)
extras_require = {
    'apptranslation': [
        'discord.py>=2.3.0',
    ],
    'bitmaphandler': [],  # No external dependencies
    'botdirectory': [
        'aiohttp>=3.9.3',
    ],
    'databasehandler': [
        'aiosqlite>=0.19.0',
        'aiomysql>=0.2.0',
        'asyncpg>=0.29.0',
        'psycopg[binary,pool]>=3.1.0',
        'motor>=3.3.0',
    ],
    'googletrans': [
        'google-cloud-translate>=3.15.3',
    ],
    'invitetracker': [
        'discord.py>=2.3.0',
    ],
    'killswitch': [
        'aiohttp>=3.9.3',
        'html2text>=2024.2.26',
        'beautifulsoup4>=4.12.3',
    ],
    'libretrans': [
        'aiohttp>=3.9.3',
    ],
    'loghandler': [
        'colorama>=0.4.6',
    ],
    'patchnotes': [
        'aiohttp>=3.9.3',
        'html2text>=2024.2.26',
        'beautifulsoup4>=4.12.3',
    ],
    'privatevoice': [
        'discord.py>=2.3.0',
    ],
    'randomusernames': [],  # No external dependencies
    'statdock': [
        'discord.py>=2.3.0',
        'pytz>=2024.2',
    ],
    'steam': [
        'aiohttp>=3.9.3',
        'beautifulsoup4>=4.12.3',
    ],
    'steamcharts': [
        'aiohttp>=3.9.3',
        'beautifulsoup4>=4.12.3',
    ],
    'twitch': [
        'aiohttp>=3.9.3',
        'requests>=2.31.0',
    ],
}

# Create 'all' extra that includes all dependencies
all_deps = set()
for deps in extras_require.values():
    all_deps.update(deps)
extras_require['all'] = sorted(all_deps)


setup(
    name='CustomModules',
    version='2.0.1',
    author='Serpensin',
    description='A collection of custom Python modules for Discord bots and utilities',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/Serpensin/CustomModules-Python',
    packages=find_packages(exclude=['tests', '*.tests', '*.tests.*', 'tests.*']),
    package_data={'CustomModules': ['py.typed']},
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
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
