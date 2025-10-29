"""Type stubs for RandomUsernames module."""
from typing import List

def generate_username(
    num_results: int = 1,
    include_numbers: bool = True
) -> List[str]:
    """Generate random usernames."""
    ...

__all__ = ['generate_username']
