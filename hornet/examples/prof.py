#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


#from hornet.examples.queens import *
from hornet.examples.symdiff import *
#from hornet.examples.fizzbuzz import *


if __name__ == '__main__':
    import cProfile
    cProfile.run('main()', sort='time')
