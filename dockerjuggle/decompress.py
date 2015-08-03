from . import docker, utils, tarutils, VERSION
import os
import tarfile
import tempfile
import collections
import time

import logging
log = logging.getLogger(__name__)

def decompress(o, i):
    with tarfile.open(fileobj=i, mode='r|*', format=tarfile.PAX_FORMAT) as input_tar:

        assert input_tar.pax_headers['docker.juggle.version'] == VERSION

        # make sure base image exists
        base_history = docker.get_image_history(input_tar.pax_headers['docker.juggle.base'])

        # save the base image
        with docker.save_image(base_history[0]) as base_tar:
            with tarfile.open(fileobj=o, mode='w|', format=tarfile.GNU_FORMAT) as output_tar:
                _decompress(output_tar, input_tar, base_tar, base_history)

def _decompress(output_tar, input_tar, base_tar, base_history):

    layers = dict()
    tmps = dict()
    tars = dict()
    hashes = collections.defaultdict(list)
    specials = []
    checksums = dict()
    index = collections.defaultdict(lambda: collections.defaultdict(list))

    try:

        # first, go through input tar to gather info about files needed from base
        for ti in input_tar:

            # see a layer directory
            if not ti.isfile():
                assert ti.isdir()
                output_tar.addfile(ti)

                # remember layer
                layers[ti.name] = True
                continue

            # copy other metadata out
            if os.path.basename(ti.name) != 'diff.tar.gz':
                output_tar.addfile(ti, input_tar.extractfile(ti))
                continue

            # deal with diff.tar.gz
            layer = os.path.dirname(ti.name)
            assert layer in layers
            assert layer not in base_history

            # remember the layer.tar has changes in it
            layers[layer] = False

            # create temp file and open it to write layer.tar
            tmps[layer] = tempfile.TemporaryFile(prefix='docker-juggle-', suffix='.tar')
            tars[layer] = tarfile.open(fileobj=tmps[layer], mode='w|', format=tarfile.GNU_FORMAT)

            # apply the diff, for this step, we are only extracting changed files
            with tarfile.open(fileobj=input_tar.extractfile(ti), mode='r|gz', format=tarfile.PAX_FORMAT) as diff_tar:
                checksums[layer] = ti.pax_headers['docker.juggle.checksum']
                _decompress_layer(tars[layer], diff_tar, specials, index, hashes[layer])

        # then, go through base tar and gather missed files
        _construct_from_base(output_tar, base_tar, layers, index)

        # last, restore special files
        _restore_special_files(specials)

        # we should not have anything left unrestored
        for layer, results in index.iteritems():
            assert len(results) == 0

        # validate checksums
        for layer, checksum in checksums.iteritems():
            computed_checksum = tarutils.checksum(hashes[layer])
            logging.debug('layer = %s, hashes = %d, checksum = %s, expected = %s', layer, len(hashes[layer]), computed_checksum, checksum)
            assert computed_checksum == checksum

        # last, write the layer.tar files in the output tar
        for layer, not_changed in layers.iteritems():
            tmp = tmps.get(layer, None)
            tar = tars.get(layer, None)

            if not tmp or not tar:
                assert not_changed is True
                assert not tmp and not tar
                continue

            _write_layer_tar(output_tar, layer, tar, tmp)

    finally:
        for tmp in tmps.values():
            tmp.close()

def _decompress_layer(layer_tar, diff_tar, specials, index, hashes):
    for ti in diff_tar:

        ti2 = tarutils.duplicate(ti)
        assert ti2.mode >= 1000

        # add directory directly
        if ti.isdir():
            layer_tar.addfile(ti2)
            hashes.append(tarutils.hash(ti2))
            continue

        # store special files for last
        if not ti.isfile():
            specials.append((layer_tar, ti2, hashes))
            continue

        # add non empty file directly
        if ti.size > 0:
            tmp, h = utils.buffer_and_hash_file(diff_tar.extractfile(ti))
            tmp.seek(0, os.SEEK_SET)
            layer_tar.addfile(ti2, tmp)
            hashes.append(tarutils.hash(ti2) + h)
            continue

        layer = ti.pax_headers.get('docker.juggle.layer', None)
        name = ti.pax_headers.get('docker.juggle.name', None)

        # add empty file directly
        if not layer or not name:
            assert not layer and not name
            layer_tar.addfile(ti2)
            hashes.append(tarutils.hash(ti2))
            continue

        # file is same from base, remember to extract it
        assert layer and name

        # remember where to put file when we found it in base
        index[layer][name].append((layer_tar, ti2, hashes))

def _construct_from_base(output_tar, base_tar, layers, index):
    for ti in base_tar:
        if not ti.isfile():
            assert ti.isdir()
            continue

        if os.path.basename(ti.name) != 'layer.tar':
            continue

        layer, _ = ti.name.split(os.path.sep)

        layer_tmp = tempfile.TemporaryFile(prefix='docker-juggle-', suffix='.tar')
        try:
            utils.buffer_copy(layer_tmp, base_tar.extractfile(ti))

            # if layer did not have a diff.tar.gz, the layer must have be identical
            # copy layer.tar directly
            layer_tarfile = None
            if layer in layers and layers[layer] is True:
                layer_tmp.seek(0, os.SEEK_SET)
                output_tar.addfile(ti, layer_tmp)

            layer_tmp.seek(0, os.SEEK_SET)
            with tarfile.open(fileobj=layer_tmp, mode='r|') as layer_tar:
                for ti in layer_tar:
                    if not ti.isfile() or ti.size <= 0:
                        continue

                    name = ti.name
                    if not isinstance(name, unicode):
                        name = name.decode('utf8')

                    results = index[layer].pop(name, None)
                    if not results:
                        continue

                    tmp, h = utils.buffer_and_hash_file(layer_tar.extractfile(ti))
                    for result in results:
                        tar, ti2, hashes = result
                        ti2.size = ti.size

                        tmp.seek(0, os.SEEK_SET)
                        tar.addfile(ti2, tmp)
                        hashes.append(tarutils.hash(ti2) + h)
        finally:
            layer_tmp.close()

def _restore_special_files(specials):
    for layer_tar, ti, hashes in specials:
        layer_tar.addfile(ti)
        hashes.append(tarutils.hash(ti))

def _write_layer_tar(output_tar, layer, tar, tmp):
    # close up layer.tar
    tar.close()

    # create a tar info
    ti = tarfile.TarInfo(name=os.path.join(layer, 'layer.tar'))
    ti.size = tmp.tell()
    ti.mtime = time.time()
    
    # write layer.tar into output tar
    tmp.seek(0, os.SEEK_SET)
    output_tar.addfile(ti, tmp)
