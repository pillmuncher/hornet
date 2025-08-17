#!/usr/bin/env python3
# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = "0.2.7"
__date__ = "2014-09-27"
__author__ = "Mick Krippendorf <m.krippendorf@freenet.de>"
__license__ = "MIT"


# from queens import *
# from symdiff import *
from fizzbuzz import *


if __name__ == "__main__":
    import cProfile

    cProfile.run("main()", sort="time")
