"""PrivateVoice module - Private voice channel management."""
import sys
import os

# Add parent directory to path to allow importing from sibling directories
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from PrivateVoice.PrivateVoice import setup, add_listener, start_garbage_collector

__all__ = ['setup', 'add_listener', 'start_garbage_collector']
