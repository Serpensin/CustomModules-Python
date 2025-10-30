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
        'aiohttp>=3.11.2',
        'discord.py>=2.4.0',
        'googletrans==4.0.0rc1',
        'httpcore==1.0.7',
        'httpx==0.28.1',
        'libretranslatepy>=2.1.3',
        'python-dotenv>=1.0.1',
        'regex>=2024.11.6',
    ],
    'bitmaphandler': [],  # No external dependencies
    'botdirectory': [
        'aiohttp>=3.11.2',
        'discord.py>=2.4.0',
    ],
    'databasehandler': [
        'aiosqlite>=0.20.0',
        'aiomysql>=0.2.0',
        'asyncpg>=0.30.0',
        'motor>=3.7.0',
    ],
    'googletrans': [
        'googletrans==4.0.0rc1',
        'httpcore==1.0.7',
        'httpx==0.28.1',
    ],
    'invitetracker': [
        'aiohttp>=3.11.2',
        'aiosqlite>=0.20.0',
        'discord.py>=2.4.0',
        'python-dotenv>=1.0.1',
    ],
    'killswitch': [
        'aiohttp>=3.11.2',
        'beautifulsoup4>=4.12.3',
    ],
    'libretrans': [
        'libretranslatepy>=2.1.3',
    ],
    'loghandler': [
        'colorama>=0.4.6',
    ],
    'patchnotes': [
        'aiohttp>=3.11.2',
        'beautifulsoup4>=4.12.3',
        'regex>=2024.11.6',
    ],
    'privatevoice': [
        'aiohttp>=3.11.2',
        'aiosqlite>=0.20.0',
        'discord.py>=2.4.0',
        'python-dotenv>=1.0.1',
    ],
    'randomusernames': [],  # No external dependencies
    'statdock': [
        'aiohttp>=3.11.2',
        'aiosqlite>=0.20.0',
        'discord.py>=2.4.0',
        'pillow>=11.0.0',
        'python-dotenv>=1.0.1',
        'pytz>=2024.2',
    ],
    'steam': [
        'aiohttp>=3.11.2',
        'beautifulsoup4>=4.12.3',
    ],
    'steamcharts': [
        'aiohttp>=3.11.2',
        'beautifulsoup4>=4.12.3',
    ],
    'twitch': [
        'aiohttp>=3.11.2',
    ],
}

# Create 'all' extra that includes all dependencies
all_deps = set()
for deps in extras_require.values():
    all_deps.update(deps)
extras_require['all'] = sorted(all_deps)


setup(
    name='CustomModules',
    version='2.0.0',
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
