"""Setup configuration for CustomModules package."""

from setuptools import setup, find_packages
import os


# Read the contents of README file
def read_file(filename):
    """Read file contents."""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# Common dependency versions
DEP_DISCORD_PY = "discord.py>=2.3.0"
DEP_AIOHTTP = "aiohttp>=3.9.3"
DEP_BEAUTIFULSOUP4 = "beautifulsoup4>=4.12.3"
DEP_HTML2TEXT = "html2text>=2024.2.26"

# Define extras for each module (using lowercase for PyPI compatibility)
extras_require = {
    "apptranslation": [
        DEP_DISCORD_PY,
    ],
    "bitmaphandler": [],  # No external dependencies
    "botdirectory": [
        DEP_AIOHTTP,
    ],
    "databasehandler": [
        "aiosqlite>=0.19.0",
        "aiomysql>=0.2.0",
        "asyncpg>=0.29.0",
        "psycopg[binary,pool]>=3.1.0",
        "motor>=3.3.0",
    ],
    "googletrans": [
        "google-cloud-translate>=3.15.3",
    ],
    "invitetracker": [
        DEP_DISCORD_PY,
    ],
    "killswitch": [
        DEP_AIOHTTP,
        DEP_HTML2TEXT,
        DEP_BEAUTIFULSOUP4,
    ],
    "libretrans": [
        DEP_AIOHTTP,
        "aiofiles>=25.1.0",
    ],
    "loghandler": [
        "colorama>=0.4.6",
    ],
    "patchnotes": [
        DEP_AIOHTTP,
        DEP_HTML2TEXT,
        DEP_BEAUTIFULSOUP4,
    ],
    "privatevoice": [
        DEP_DISCORD_PY,
    ],
    "randomusernames": [],  # No external dependencies
    "statdock": [
        DEP_DISCORD_PY,
        "pytz>=2024.2",
    ],
    "steam": [
        DEP_AIOHTTP,
        DEP_BEAUTIFULSOUP4,
    ],
    "steamcharts": [
        DEP_AIOHTTP,
        DEP_BEAUTIFULSOUP4,
    ],
    "twitch": [
        DEP_AIOHTTP,
        "requests>=2.31.0",
    ],
}

# Create 'all' extra that includes all dependencies
all_deps = set()
for deps in extras_require.values():
    all_deps.update(deps)
extras_require["all"] = sorted(all_deps)


setup(
    name="CustomModules",
    version="3.1.1",
    author="Serpensin",
    description="A collection of custom Python modules for Discord bots and utilities",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/Serpensin/CustomModules-Python",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    package_data={"CustomModules": ["py.typed"]},
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
    ],
    python_requires=">=3.10,<3.14",
    install_requires=[],  # No core dependencies
    extras_require=extras_require,
    license="AGPL-3.0",
    keywords="discord bot utilities modules custom",
    project_urls={
        "Bug Reports": "https://github.com/Serpensin/CustomModules-Python/issues",
        "Source": "https://github.com/Serpensin/CustomModules-Python",
    },
)
