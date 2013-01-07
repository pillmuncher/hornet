hornet
======

Prolog as Embedded DSL for Python 3.3.

Just something I did over the holidays.

The files examples.py, hanoi.py and parsing.py illustrate how one would use hornet.
hanoi.py is modified version of minimal_hanoi.py that comes with Python in the 
Lib\turtledemo directory.

expressions.py contains some kind of monadic expression tree combinators,
hence the name: Horn clauses for Python via Expression Trees.

The DSL is Prolog-like, as close as one could get using only Pythons operators.
Instead of the comma I use '&', instead of ':-' I use '<<' and since hornet also
understands (well, part of) DCG rules, '-->' becomes '>>'.

resolver.py contains the SLD Resolver. It's implementation is naive and slow. My goal was
not to write a fast Prolog engine in Python, but to play around with new stuff that comes
with Python 3.3, and also to find out if it'd be possible to create an Embedded DSL like that.

Maybe I replace it by a WAM-based version one day, after I finished reading Ait-Kaci's book.

system.py contains system predicates like member/2, reverse/2 and so on.

util.py contains some helper functions.
