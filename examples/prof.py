# Copyright (c) 2014 Mick Krippendorf <m.krippendorf+hornet@posteo.de>

# from queens import *
# from symdiff import *
from examples.fizzbuzz import *

if __name__ == "__main__":
    import cProfile

    cProfile.run("main()", sort="time")
