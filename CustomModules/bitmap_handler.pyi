"""Type stubs for BitmapHandler module."""
from typing import Tuple, Optional

class BitmapHandler:
    """Bitmap manipulation and handling."""
    
    def __init__(self) -> None: ...
    
    @staticmethod
    def create_bitmap(
        width: int,
        height: int,
        color: Tuple[int, int, int] = (255, 255, 255)
    ) -> bytes: ...
    
    @staticmethod
    def save_bitmap(data: bytes, filename: str) -> None: ...
    
    @staticmethod
    def load_bitmap(filename: str) -> bytes: ...

__all__ = ['BitmapHandler']
