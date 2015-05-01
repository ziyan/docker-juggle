# -*- coding: utf-8 -*-
# Copyright (C) 2015 MUJIN Inc
from distutils.core import setup

setup(
    name='dockerjuggle',
    long_description='Docker image differential compression and decompression',
    version='0.1.0',
    packages=['dockerjuggle'],
    license='MIT',
    scripts=[
    	'bin/docker-juggle-compress',
    	'bin/docker-juggle-decompress',
    ]
)
