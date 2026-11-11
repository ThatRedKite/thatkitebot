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

#region imports
import atexit
import ctypes
import mmap
import os
import platform
import secrets

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
#endregion

KEY_SIZE = 32
NONCE_SIZE = 12
SYS_MEMFD_SECRET = 447  # Linux x86_64 and aarch64
MESSAGE_PREFIX = b"TKBMSG\x01"


class MessageCacheCipher:
    def __init__(self):
        self.enabled = bool(int(os.getenv("ENCRYPT_MESSAGE_CACHE", "1")))
        self.fd = None
        self.region = None

        if not self.enabled:
            return

        if platform.system() != "Linux" or platform.machine() not in ("x86_64", "aarch64"):
            raise RuntimeError("Message cache encryption requires Linux x86_64/aarch64 with memfd_secret support")

        libc = ctypes.CDLL(None, use_errno=True)
        libc.syscall.restype = ctypes.c_long
        fd = libc.syscall(ctypes.c_long(SYS_MEMFD_SECRET), ctypes.c_uint(os.O_CLOEXEC))
        if fd < 0:
            err = ctypes.get_errno()
            raise OSError(err, "memfd_secret failed: " + os.strerror(err) +
                          ". Message cache encryption requires kernel support, an allowing seccomp policy, and a large enough memlock allowance")

        region = None
        try:
            os.ftruncate(fd, mmap.PAGESIZE)
            region = mmap.mmap(fd, mmap.PAGESIZE, flags=mmap.MAP_SHARED,
                               prot=mmap.PROT_READ | mmap.PROT_WRITE)
            region[:KEY_SIZE] = secrets.token_bytes(KEY_SIZE)
        except BaseException:
            if region is not None:
                region.close()
            os.close(fd)
            raise

        self.fd = fd
        self.region = region
        atexit.register(self.close)

    def encrypt(self, data: bytes, key: str) -> bytes:
        if not self.enabled:
            return data

        nonce = secrets.token_bytes(NONCE_SIZE)
        # Read the key from secret memory and create a temporary cipher for this operation
        cipher = AESGCM(self.region[:KEY_SIZE])
        return MESSAGE_PREFIX + nonce + cipher.encrypt(nonce, data, key.encode("ASCII"))

    def decrypt(self, data: bytes, key: str):
        if not self.enabled:
            return None if data.startswith(MESSAGE_PREFIX) else data

        if not data.startswith(MESSAGE_PREFIX):
            return None

        offset = len(MESSAGE_PREFIX)
        nonce = data[offset:offset + NONCE_SIZE]
        ciphertext = data[offset + NONCE_SIZE:]
        try:
            cipher = AESGCM(self.region[:KEY_SIZE])
            return cipher.decrypt(nonce, ciphertext, key.encode("ASCII"))
        except (InvalidTag, ValueError):
            # if we can't decrypt, return None to indicate a cache miss or expired data
            return None

    def close(self):
        if self.region is not None:
            self.region[:KEY_SIZE] = bytes(KEY_SIZE)
            self.region.close()
            self.region = None
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
