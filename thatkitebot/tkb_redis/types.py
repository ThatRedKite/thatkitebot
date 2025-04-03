#region License
"""
MIT License

Copyright (c) 2019-present The Kitebot Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
#endregion

import redis as syncredis

from collections.abc import MutableMapping, MutableSet
from .util import compress_data, decompress_data

class RedisType:
    def __init__(self, redis: syncredis.Redis, name:str):
        self.name = name
        self.redis = redis


class RedisHash(RedisType, MutableMapping):
    def __getitem__(self, key):
        return self.redis.hget(self.name, key)

    def __iter__(self):
        return self.redis.hscan_iter(self.name, "*")

    def __delitem__(self, key):
        return self.redis.hdel(self.name, key)

    def __contains__(self, key):
        return self.redis.hget(self.name, key) is not None

    def __len__(self):
        return self.redis.hlen(self.name)

    def __repr__(self):
        return self.redis.hgetall(self.name).__repr__()

    def __dir__(self):
        return self.redis.hgetall(self.name).__dir__()

    def __setitem__(self, key, value):
        return self.redis.hset(self.name, key, value)

    def __eq__(self, other):
        if isinstance(other, self) and other.name == self.name:
            return True

        elif isinstance(other, dict):
            data = self.redis.hgetall(self.name)
            return data == other
        else:
            return False
        
class CompressedRedisDict(MutableMapping):
    def __init__(self, redis: syncredis.Redis, name:str, quality=11):
        self.redis = redis
        self.quality = quality
        self.name = name

        super().__init__()

    def __getitem__(self, key):
        return decompress_data(self.redis.get(self.name, self.name), self.quality)[key]
    
    def __setitem__(self, key, value):
        data_new = decompress_data(self.redis.get(self.name, self.name), self.quality)
        data_new[key] = value
        return self.redis.set(self.name, compress_data(data_new, self.quality))
    
    def __len__(self):
        all = decompress_data(self.redis.get(self.name))
        return len(all)
    
    def __delitem__(self, key):
        data: dict = decompress_data(self.redis.get(self.name, self.name), self.quality)[key]
        data.pop(key)
        return self.redis.set(self.name, compress_data(data, self.quality))
    
    def __iter__(self):
        return decompress_data(self.redis.get(self.name, self.name), self.quality).__iter__()

