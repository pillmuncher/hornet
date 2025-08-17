# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

# from queens import *
# from symdiff import *
from fizzbuzz import *

if __name__ == "__main__":
    import cProfile

    cProfile.run("main()", sort="time")
