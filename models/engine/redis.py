#!/usr/i/env python3
import redis
import os

class Redis:
    def __init__(self):
        self.redis = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), 
                                 port=os.getenv('REDIS_PORT', 6379), db=0)

    def publish(self, channel, data):
        self.publish(channel, data)

    def pubsub(self):
        return self.redis.pubsub()

    def all(self):
        keys = self.redis.keys()
        return {key.decode('utf-8'): self.redis.get(key).decode('utf-8') for key in keys}
    
    def count(self):
        return len(self.all())
    
    def get(self, key):
        value = self.redis.get(key)
        return value.decode('utf-8') if value else None
    
    def set(self, key, value):
        if len(key) < 0 or key is None:
            raise ValueError('Key cannot be empty or None')
        if (isinstance(value, str) and len(value) == 0) or value is None:
            raise ValueError('Value cannot be empty or None')
        return self.redis.set(key, value)
    
    def delete(self, key):
        retval = self.redis.delete(key)
        if retval == 0:
            raise KeyError(f"Key '{key}' does not exist")
    
    def exists(self, key):
        return self.redis.exists(key)
    
    def flush(self):
        return self.redis.flushdb()