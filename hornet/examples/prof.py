#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hornet.examples.symdiff import *
#from hornet.examples.fizzbuzz import *


if __name__ == '__main__':
    import cProfile
    cProfile.run('main()', sort='time')
