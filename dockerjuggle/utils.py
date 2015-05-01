import hashlib
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import logging
log = logging.getLogger(__name__)

def create_buffer():
    return StringIO()

def hash_file(f):
    hasher = hashlib.sha256()
    while True:
        buf = f.read(4096)
        if not buf:
            break
        hasher.update(buf)
    return hasher.hexdigest()

def buffer_and_hash_file(f):
    tmp = create_buffer()
    hasher = hashlib.sha256()
    while True:
        buf = f.read(4096)
        if not buf:
            break
        tmp.write(buf)
        hasher.update(buf)
    return tmp, hasher.hexdigest()

def buffer_file(f):
    tmp = create_buffer()
    while True:
        buf = f.read(4096)
        if not buf:
            break
        tmp.write(buf)
    return tmp

def hash(data, f=None):
    return hashlib.sha256(data).hexdigest()
