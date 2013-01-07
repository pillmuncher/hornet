hornet
======

A Prolog-like Embedded DSL for Python 3.3.

Just something I did over the holidays.

It provides a way to program prolog in Python - sort of. The syntax is of course different,
and at the moment there are only few system predicates implemented. It is very easy to 
interface with Python, since it is Python. See hanoi.py for an example. It is a modified
version of minimal_hanoi.py that comes with Python in the Lib\turtledemo directory. Instead
of the original version it uses hornet to compute the hanoi algorithm.

parsing.py contains some DCG rules for some (about 13400, actually) meaningless german
sentences. It exists only so I can see if my DCG translation works.

examples.py illustrates some more stuff that is possible with hornet.

expressions.py contains some kind of monadic expression tree combinators,
hence the name: Horn clauses via Expression Trees.

The DSL is Prolog-like, as close as one could get using only Pythons operators.
Instead of the comma to seperate goals in a clause's body, I use '&', instead of ':-' I use
'<<', and since hornet also understands (well, part of) DCG rules, '-->' becomes '>>'.

resolver.py contains the SLD Resolver. It's implementation is semi-naive and slow. My goal was
not to write a fast Prolog engine in Python, but to play around with new stuff that comes
with Python 3.3, and also to find out if it'd be possible to create an Embedded DSL like that.

Maybe I'll replace it by a WAM-based version one day, after I finished reading Ait-Kaci's book.

system.py contains system predicates like member/2, reverse/2, true/0, cut/0 and so on.

util.py contains some helper functions.
