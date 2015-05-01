from . import docker, utils, VERSION
import os
import tarfile

try:
    import simplejson as json
except ImportError:
    import json

import logging
log = logging.getLogger(__name__)

def index(image):
    home_dir = os.environ.get('HOME', '~')
    index_dir = os.path.join(home_dir, '.docker-juggle', VERSION, 'index')
    if not os.path.exists(index_dir):
        os.makedirs(index_dir)

    index_path = os.path.join(index_dir, '%s.json' % image)
    if os.path.exists(index_path):
        with open(index_path, 'rb') as f:
            return json.load(f)

    with docker.save_image(image) as t:
        index = _index_image(t)
        with open(index_path, 'wb') as f:
            json.dump(index, f, sort_keys=True, indent=4, separators=(',', ': '))
        return index

def _index_image(t):
    index = dict()
    for ti in t:

        if not ti.isfile():
            continue

        if os.path.basename(ti.name) != 'layer.tar':
            continue

        layer, _ = ti.name.split(os.path.sep)
        log.info('indexing: %s ...' % layer)

        with tarfile.open(fileobj=t.extractfile(ti), mode='r|') as t2:
            for ti2 in t2:

                # do not index small files, they cannot be compressed efficiently
                if not ti2.isfile() or ti2.size <= 0:
                    continue

                # hash file content
                h = utils.hash_file(t2.extractfile(ti2))
                index[h] = [layer, ti2.name]

    return index
