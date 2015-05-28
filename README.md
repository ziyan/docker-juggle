docker-juggle
=============

This util helps compressing docker images before manually moving them to other hosts. This is especially useful if you have large docker images and layers that you make minor incremental changes to, and that your environment prevents you from using a docker registry.

Install
-------

```shell
pip install git+https://github.com/ziyan/docker-juggle.git
```

Compress
--------

```shell
docker save <image-tag> | docker-juggle-compress <previous-known-image-tag> > compressed.tar.gz
```

Decompress
----------

```shell
cat compressed.tar.gz | docker-juggle-decompress | docker load
```

