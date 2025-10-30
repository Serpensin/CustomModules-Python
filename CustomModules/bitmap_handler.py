import logging
from typing import Dict, List, Optional, Union


class BitmapHandler:
    def __init__(self, keys: List[str], logger: Optional[logging.Logger] = None):
        """
        Initialize the BitmapHandler with a list of keys.

        Args:
            keys (List[str]): A list of keys to initialize the bitmap.
            A maximum of 64 keys can be provided.
            logger (Optional[logging.Logger]): Parent logger. If provided, creates a child logger
            under CustomModules.BitmapHandler. Defaults to None.

        Raises:
            ValueError: If more than 64 keys are provided.
        """
        # Setup logger with child hierarchy: parent -> CustomModules -> BitmapHandler
        if logger:
            self.logger = logger.getChild("CustomModules").getChild("BitmapHandler")
        else:
            self.logger = logging.getLogger("CustomModules.BitmapHandler")

        self.logger.debug(f"Initializing BitmapHandler with {len(keys)} keys")

        if len(keys) > 64:
            self.logger.error(f"Too many keys provided: {len(keys)} > 64")
            raise ValueError(
                "Warning: You are trying to initialize with more than 64 keys. This may exceed the limit for bit manipulation."
            )

        # Generate the bitmap dictionary dynamically
        self.bitmap: Dict[str, int] = {key: index for index, key in enumerate(keys)}
        self.key_list: List[str] = keys.copy()  # Store keys in a list for ordering

        self.logger.info(
            f"BitmapHandler initialized successfully with keys: {', '.join(keys)}"
        )

    def get_bitkey(self, *args: str) -> int:
        """
        Converts a list of keys into a single bitkey.

        Args:
            *args (str): A variable number of keys to be converted to a bitkey.

        Returns:
            int: The bitkey representing the provided keys.

        Raises:
            KeyError: If any key is invalid (not in the bitmap).
        """
        self.logger.debug(f"Converting keys to bitkey: {args}")
        bitkey = 0
        for key in args:
            if key in self.bitmap:
                bitkey |= 1 << self.bitmap[key]
                self.logger.debug(
                    f"Added key '{key}' at position {self.bitmap[key]} to bitkey"
                )
            elif key:
                self.logger.error(f"Invalid key provided: {key}")
                raise KeyError(f"Invalid key: {key}")

        self.logger.debug(f"Generated bitkey: {bitkey} (binary: {bin(bitkey)})")
        return bitkey

    def check_key_in_bitkey(self, key: str, bitkey: int) -> bool:
        """
        Checks if a given key is present in the bitkey.

        Args:
            key (str): The key to check.
            bitkey (int): The bitkey in which to check for the key.

        Returns:
            bool: True if the key is present in the bitkey, False otherwise.
        """
        result = key in self.bitmap and bool(bitkey & (1 << self.bitmap[key]))
        self.logger.debug(f"Checking if key '{key}' is in bitkey {bitkey}: {result}")
        return result

    def get_active_keys(
        self, bitkey: int, single: bool = False
    ) -> Union[str, List[str]]:
        """
        Retrieves the active keys from a bitkey.

        Args:
            bitkey (int): The bitkey from which to retrieve active keys.
            single (bool, optional): If True, returns the last active key as a string.
            If False, returns a list of active keys. Defaults to False.

        Returns:
            Union[str, List[str]]: The active keys in the bitkey.

        Raises:
            ValueError: If the bitkey is invalid (not within the valid range).
        """
        self.logger.debug(
            f"Retrieving active keys from bitkey {bitkey} (single={single})"
        )

        max_bitkey = (1 << len(self.bitmap)) - 1
        if bitkey < 0 or bitkey > max_bitkey:
            self.logger.error(
                f"Invalid bitkey: {bitkey}. Must be between 0 and {max_bitkey}"
            )
            raise ValueError(
                f"Invalid bitkey: {bitkey}. It must be between 0 and {max_bitkey}."
            )

        active_keys = [
            key
            for key, bit_position in self.bitmap.items()
            if bitkey & (1 << bit_position)
        ]

        self.logger.debug(f"Found {len(active_keys)} active keys: {active_keys}")

        if single:
            result = active_keys[-1] if active_keys else ""
            self.logger.debug(f"Returning single active key: '{result}'")
            return result
        return active_keys

    def toggle_key_in_bitkey(self, key: str, bitkey: int, add: bool = True) -> int:
        """
        Adds or removes a given key from an existing bitkey based on the 'add' parameter.

        Args:
            key (str): The key to add or remove.
            bitkey (int): The existing bitkey.
            add (bool, optional): If True, the key is added to the bitkey;
            if False, the key is removed. Defaults to True.

        Returns:
            int: The updated bitkey after the operation.

        Raises:
            KeyError: If the key is invalid (not in the bitmap).
        """
        self.logger.debug(f"Toggling key '{key}' in bitkey {bitkey} (add={add})")

        if key not in self.bitmap:
            self.logger.error(f"Invalid key: {key}")
            raise KeyError(f"Invalid key: {key}")

        result = (
            bitkey | (1 << self.bitmap[key])
            if add
            else bitkey & ~(1 << self.bitmap[key])
        )

        self.logger.debug(
            f"Key '{key}' {'added to' if add else 'removed from'} bitkey. Result: {result}"
        )
        return result

    def invert_bitkey(self, bitkey: int) -> int:
        """
        Inverts all bits in the given bitkey.

        Args:
            bitkey (int): The bitkey to be inverted.

        Returns:
            int: The inverted bitkey.
        """
        max_bitkey = (1 << len(self.bitmap)) - 1
        result = ~bitkey & max_bitkey
        self.logger.debug(f"Inverted bitkey {bitkey} to {result}")
        return result

    def count_active_bits(self, bitkey: int) -> int:
        """
        Counts the number of active (set) bits in the bitkey.

        Args:
            bitkey (int): The bitkey for which to count active bits.

        Returns:
            int: The count of active bits in the bitkey.
        """
        count = bin(bitkey).count("1")
        self.logger.debug(f"Counted {count} active bits in bitkey {bitkey}")
        return count

    def compare_bitkeys(self, bitkey1: int, bitkey2: int) -> Dict[str, List[str]]:
        """
        Compares two bitkeys and returns a dictionary of differences.

        Args:
            bitkey1 (int): The first bitkey to compare.
            bitkey2 (int): The second bitkey to compare.

        Returns:
            Dict[str, List[str]]: A dictionary containing the common keys,
            keys only in the first bitkey, and keys only in the second bitkey.
        """
        self.logger.debug(f"Comparing bitkeys: {bitkey1} and {bitkey2}")

        common = bitkey1 & bitkey2
        only_in_1 = bitkey1 & ~bitkey2
        only_in_2 = bitkey2 & ~bitkey1

        # get_active_keys with single=False always returns List[str]
        common_keys = self.get_active_keys(common, single=False)
        only_in_1_keys = self.get_active_keys(only_in_1, single=False)
        only_in_2_keys = self.get_active_keys(only_in_2, single=False)

        result = {
            "common_keys": (
                common_keys if isinstance(common_keys, list) else [common_keys]
            ),
            "only_in_bitkey1": (
                only_in_1_keys if isinstance(only_in_1_keys, list) else [only_in_1_keys]
            ),
            "only_in_bitkey2": (
                only_in_2_keys if isinstance(only_in_2_keys, list) else [only_in_2_keys]
            ),
        }

        self.logger.debug(
            f"Comparison result: {len(result['common_keys'])} common, "
            f"{len(result['only_in_bitkey1'])} only in first, "
            f"{len(result['only_in_bitkey2'])} only in second"
        )

        return result

    def add_key(self, key: str):
        """
        Adds a new key to the bitmap.

        Args:
            key (str): The key to add.

        Raises:
            KeyError: If the key already exists in the bitmap.
        """
        self.logger.debug(f"Attempting to add key: {key}")

        if key in self.bitmap:
            self.logger.error(f"Key '{key}' already exists in bitmap")
            raise KeyError(f"Key '{key}' already exists.")

        # Add the new key and update the bitmap and key_list
        new_index = len(self.bitmap)
        self.bitmap[key] = new_index  # Assign the next available index
        self.key_list.append(key)  # Append the new key to the list

        self.logger.info(
            f"Added key '{key}' at position {new_index}. Total keys: {len(self.bitmap)}"
        )

    def remove_key(self, key: str):
        """
        Removes a key from the bitmap.

        Args:
            key (str): The key to remove.

        Raises:
            KeyError: If the key does not exist in the bitmap.
        """
        self.logger.debug(f"Attempting to remove key: {key}")

        if key not in self.bitmap:
            self.logger.error(f"Key '{key}' does not exist in bitmap")
            raise KeyError(f"Key '{key}' does not exist.")

        # Remove the key and reassign indices for the remaining keys
        index_to_remove = self.bitmap[key]
        del self.bitmap[key]

        # Reassign keys and their bit positions only if the key is not the last one
        if len(self.bitmap) > 0:
            for k in self.bitmap:
                if self.bitmap[k] > index_to_remove:
                    self.bitmap[k] -= 1

        self.key_list.remove(key)  # Remove from key list

        self.logger.info(
            f"Removed key '{key}' from position {index_to_remove}. Remaining keys: {len(self.bitmap)}"
        )

    def get_keys(self) -> Dict[str, int]:
        """
        Returns the current bitmap dictionary.

        Returns:
            Dict[str, int]: The current bitmap dictionary mapping keys to their bit positions.
        """
        self.logger.debug(f"Retrieving bitmap with {len(self.bitmap)} keys")
        return self.bitmap
