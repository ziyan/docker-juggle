from . import docker, index, utils, tarutils, VERSION
import os
import tarfile

try:
    import simplejson as json
except ImportError:
    import json

import logging
log = logging.getLogger(__name__)

def compress(o, i, base):

    # get history of images
    base_history = docker.get_image_history(base)
    base_index = index.index(base_history[0])

    with tarfile.open(fileobj=i, mode='r|')  as input_tar:

        # compress
        headers = {
            'docker.juggle.version': VERSION,
            'docker.juggle.base': base_history[0],
        }
        with tarfile.open(fileobj=o, mode='w|gz', format=tarfile.PAX_FORMAT, pax_headers=headers) as output_tar:
            _compress(output_tar, input_tar, base_history, base_index)

def _compress(output_tar, input_tar, base_history, base_index):

    for ti in input_tar:

        # add directories
        if not ti.isfile():
            assert ti.isdir()
            output_tar.addfile(ti)
            continue

        # copy meta data
        if os.path.basename(ti.name) != 'layer.tar':
            output_tar.addfile(ti, input_tar.extractfile(ti))
            continue

        layer = os.path.dirname(ti.name)
        log.info('compressing: %s ...' % layer)

        # if layer is the same in both images
        # only create the layer directory with meta data
        if layer in base_history:
            continue

        # create a temp file to hold the diff tar output
        tmp = utils.create_buffer()

        # compress layer
        checksum = None
        with tarfile.open(fileobj=input_tar.extractfile(ti), mode='r|') as layer_tar:
            with tarfile.open(fileobj=tmp, mode='w|gz', format=tarfile.PAX_FORMAT) as diff_tar:
                hashes = _compress_layer(diff_tar, layer_tar, base_index)
                checksum = tarutils.checksum(hashes)
                logging.debug('layer = %s, hashes = %d, checksum = %s', layer, len(hashes), checksum)

        # add to output
        ti.size = tmp.tell()
        ti.name = os.path.join(layer, 'diff.tar.gz')
        ti.pax_headers['docker.juggle.checksum'] = checksum

        tmp.seek(0, os.SEEK_SET)
        output_tar.addfile(ti, tmp)


def _compress_layer(diff_tar, layer_tar, base_index):
    hashes = []

    # add each member of layer
    for ti in layer_tar:
        ti2 = tarutils.duplicate(ti)

        # for non-file members, add them directly
        if not ti.isfile():
            hashes.append(tarutils.hash(ti))
            diff_tar.addfile(ti2)
            continue

        # add small files directly
        if ti.size <= 0:
            hashes.append(tarutils.hash(ti))
            diff_tar.addfile(ti2)
            continue

        # calculate hash for file
        tmp, h = utils.buffer_and_hash_file(layer_tar.extractfile(ti))
        results = base_index.get(h, None)
        hashes.append(tarutils.hash(ti) + h)

        # if file content is new, make a copy in the diff tar
        if not results:
            tmp.seek(0, os.SEEK_SET)
            diff_tar.addfile(ti2, tmp)
            log.info('\t%s' % ti.name)
            continue

        # otherwise, simply add pointer to the existing file
        layer, name = results

        ti2.size = 0
        ti2.pax_headers['docker.juggle.layer'] = layer
        ti2.pax_headers['docker.juggle.name'] = name
        diff_tar.addfile(ti2)

    return hashes
