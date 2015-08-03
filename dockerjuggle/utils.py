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
        buf = f.read(1024*1024)
        if not buf:
            break
        hasher.update(buf)
    return hasher.hexdigest()

def buffer_and_hash_file(f):
    tmp = create_buffer()
    hasher = hashlib.sha256()
    while True:
        buf = f.read(1024*1024)
        if not buf:
            break
        tmp.write(buf)
        hasher.update(buf)
    return tmp, hasher.hexdigest()

def buffer_file(f):
    tmp = create_buffer()
    buffer_copy(tmp, f)
    return tmp

def buffer_copy(dst, src):
    while True:
        buf = src.read(1024*1024)
        if not buf:
            break
        dst.write(buf)

def hash(data):
    return hashlib.sha256(data).hexdigest()
