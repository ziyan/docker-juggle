docker-juggle
=============

This util helps compressing docker images before manually moving them to other hosts. This is especially useful if you have large docker images and layers that you make minor incremental changes to, and that your environment prevents you from using a docker registry.

Compress
--------

``
docker save <image-tag> | docker-juggle-compress <previous-known-image-tag> > compressed.tar.gz
``

Decompress
----------

``
cat compressed.tar.gz | docker-juggle-decompress | docker load
``

