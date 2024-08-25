"""
Simple key-value store
using file system.
"""
from pathlib import Path
import re
import pickle

key_pattern = re.compile(r'^[-_a-zA-Z0-9]+$')


def validate_key(key):
    if not key_pattern.match(key):
        raise ValueError(
            f'Invalid key: {key}, valid pattern={key_pattern.pattern}')


class AbstractKVStore:
    def get(self, key, default=None):
        """
        Get value by key.
        """
        raise NotImplementedError

    def set(self, key, value):
        """
        Put value by key.
        """
        raise NotImplementedError


class SimpleKVStore(AbstractKVStore):

    def __init__(self):
        self.storage_path = Path(__file__).parent / 'storage'

    def get(self, key, default=None):
        """
        Get value by key.
        """
        validate_key(key)
        storage_file = self.storage_path / key
        try:
            return pickle.loads(storage_file.read_bytes())
        except FileNotFoundError:
            return default

    def set(self, key, value):
        """
        Put value by key.
        """
        validate_key(key)
        storage_file = self.storage_path / key
        storage_file.write_bytes(pickle.dumps(value))
