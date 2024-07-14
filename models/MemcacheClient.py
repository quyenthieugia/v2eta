from pymemcache.client.base import Client

class MemcacheClient:
    def __init__(self, host='127.0.0.1', port=11211):
        # Initialize the Memcached client
        self.client = Client((host, port))
        print(f"Memcached client initialized on {host}:{port}")

    def set_value(self, key, value):
        # Set a key-value pair in the cache
        self.client.set(key, value)
        print(f"Value set in cache: {key} -> {value}")

    def get_value(self, key):
        # Get the value from the cache
        value = self.client.get(key)
        if value:
            print(f"Retrieved value from cache: {key} -> {value.decode('utf-8')}")
            return value.decode('utf-8')
        else:
            print(f"Key not found in cache: {key}")
            return None

    def delete_value(self, key):
        # Delete the key from the cache
        self.client.delete(key)
        print(f"Key deleted from cache: {key}")