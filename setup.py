#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>


import os
from setuptools import setup
import ez_setup
ez_setup.use_setuptools()


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


setup(
    name="hornet",
    version="0.3.0a0",
    author="Mick Krippendorf",
    author_email="m.krippendorf@freenet.de",
    description="Horn clauses via Expression Trees",
    license="MIT",
    keywords="logic-programming prolog",
    url="https://github.com/pillmuncher/hornet",
    packages=['hornet', 'hornet.examples'],
    install_requires=['codegen'],
    package_data={'hornet': ['../*.md']},
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Libraries",
        "License :: OSI Approved :: MIT License",
    ],
)
