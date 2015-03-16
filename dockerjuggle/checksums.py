# -*- coding: utf-8 -*-

import hashlib

def sha256_file(fp):
    h = hashlib.sha256(data or '')
    if not fp:
        return h.hexdigest()
    while True:
        buf = fp.read(4096)
        if not buf:
            break
        h.update(buf)
    return h.hexdigest()

def sha256_string(s):
    return hashlib.sha256(s).hexdigest()

class TarSum(object):

    def __init__(self):
        self.header_fields = (
            'name',
            'mode',
            'uid',
            'gid',
            'size',
            'type',
            'linkname',
            'uname',
            'gname',
            'devmajor',
            'devminor',
        )
        self.hashes = []

    def append(self, member, tar):
        header = ''
        for field in self.header_fields:
            value = getattr(member, field)
            if field == 'type':
                field = 'typeflag'
            elif field == 'name':
                if member.isdir() and not value.endswith('/'):
                    value += '/'
            header += '{0}{1}'.format(field, value)
        h = None
        try:
            if member.size > 0:
                f = tar.extractfile(member)
                h = sha256_file(f, header)
            else:
                h = sha256_string(header)
        except KeyError:
            h = sha256_string(header)
        self.hashes.append(h)

    def compute(self):
        self.hashes.sort()
        data = ''.join(self.hashes)
        tarsum = 'tarsum+sha256:{0}'.format(sha256_string(data))
        return tarsum

if __name__ == '__main__':
    import tarfile
    tarsum = TarSum()
    tar = tarfile.open('/tmp/docker-juggle-save-toG8Pq/c4c3752af388b4d459fd93e1ecff9a91265c8eabf365bcf84c4ee2d80923cbe3/c4c3752af388b4d459fd93e1ecff9a91265c8eabf365bcf84c4ee2d80923cbe3/layer.tar')
    for member in tar:
        tarsum.append(member, tar)
    print tarsum.compute()
    tar.close()
