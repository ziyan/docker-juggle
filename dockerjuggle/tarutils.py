from . import utils
import tarfile
import time
import struct

import logging
log = logging.getLogger(__name__)

class TarInfo(tarfile.TarInfo):
    def get_info(self, encoding, errors):
        """Return the TarInfo's attributes as a dictionary.
        """
        info = {
            "name":     self.name,
            "mode":     self.mode,
            "uid":      self.uid,
            "gid":      self.gid,
            "size":     self.size,
            "mtime":    self.mtime,
            "chksum":   self.chksum,
            "type":     self.type,
            "linkname": self.linkname,
            "uname":    self.uname,
            "gname":    self.gname,
            "devmajor": self.devmajor,
            "devminor": self.devminor
        }

        if info["type"] == tarfile.DIRTYPE and not info["name"].endswith("/"):
            info["name"] += "/"

        for key in ("name", "linkname", "uname", "gname"):
            if type(info[key]) is unicode:
                info[key] = info[key].encode(encoding, errors)

        return info

    @staticmethod
    def _create_header(info, format):
        """Return a header block. info is a dictionary with file
           information, format must be one of the *_FORMAT constants.
        """
        parts = [
            tarfile.stn(info.get("name", ""), 100),
            tarfile.itn(info.get("mode", 0), 8, format),
            tarfile.itn(info.get("uid", 0), 8, format),
            tarfile.itn(info.get("gid", 0), 8, format),
            tarfile.itn(info.get("size", 0), 12, format),
            tarfile.itn(info.get("mtime", 0), 12, format),
            "        ", # checksum field
            info.get("type", tarfile.REGTYPE),
            tarfile.stn(info.get("linkname", ""), 100),
            tarfile.stn(info.get("magic", tarfile.POSIX_MAGIC), 8),
            tarfile.stn(info.get("uname", ""), 32),
            tarfile.stn(info.get("gname", ""), 32),
            tarfile.itn(info.get("devmajor", 0), 8, format),
            tarfile.itn(info.get("devminor", 0), 8, format),
            tarfile.stn(info.get("prefix", ""), 155)
        ]

        buf = struct.pack("%ds" % tarfile.BLOCKSIZE, "".join(parts))
        chksum = tarfile.calc_chksums(buf[-tarfile.BLOCKSIZE:])[0]
        buf = buf[:-364] + "%06o\0" % chksum + buf[-357:]
        return buf


HEADERS = [
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
]

def duplicate(original):
    ti = TarInfo()
    for field in HEADERS:
        setattr(ti, field, getattr(original, field))
    ti.mtime = time.time()
    return ti

def hash(ti):
    header = ''
    for field in HEADERS:
        value = getattr(ti, field)
        if field == 'type':
            field = 'typeflag'
        elif field == 'name':
            if ti.isdir() and not value.endswith('/'):
                value += '/'
        header += '{0}{1}'.format(field, value)
    return utils.hash(header)

def checksum(hashes):
    hashes.sort()
    return utils.hash(','.join(hashes))
