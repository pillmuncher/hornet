# Hornet

**Horn clauses via Expression Trees** — a Prolog-like embedded DSL for Python ≥ 3.13.

Hornet lets you write logic programs directly in Python. Instead of parsing Prolog strings, it hijacks Python's operator overloading and `__call__` syntax to build expression trees, which a resolution engine then solves via unification and backtracking.

---

## Installation

```bash
pip install hornet-dsl
```

Requires Python 3.13+. Dependencies: `toolz`, `immutables`.

---

## Core Concepts

### Terms

Hornet's term algebra mirrors Prolog's:

| Hornet | Prolog equivalent |
|---|---|
| `Variable('X')` / `symbols.X` | `X` (logic variable) |
| `Atom('foo')` / `symbols.foo` | `foo` (atom) |
| `symbols.foo(X, Y)` | `foo(X, Y)` (compound term) |
| `[1, 2, 3]` / `promote([1,2,3])` | `[1,2,3]` (list) |
| `[H \| T]` via `BitOr` | `[H\|T]` (cons cell) |

Import symbols dynamically from `hornet.symbols`. Names starting with uppercase become `Variable`s; lowercase become `Atom`s; `_` is the anonymous wildcard.

```python
from hornet.symbols import X, Y, parent, mortal, human
```

### Facts and Rules

Facts and rules are built with `.when()`:

```python
db.tell(
    parent('socrates', 'sophroniscus'),   # fact
    human('socrates'),                    # fact
    mortal(X).when(human(X)),             # rule: mortal(X) :- human(X).
)
```

### Queries

```python
from hornet import database
from hornet.symbols import X, mortal, human

db = database()
db.tell(human('socrates'))
db.tell(mortal(X).when(human(X)))

for subst in db.ask(mortal(X)):
    print(subst[X])   # → socrates
```

`db.ask()` returns an iterable of substitutions. Each substitution maps variables to their bound values.

---

## Arithmetic

Arithmetic expressions are built using Python's operators on symbolic terms and evaluated lazily by `let`:

```python
>>> from hornet.symbols import X, Y, R, let, equal
>>> from hornet import database
>>> db = database()
>>> for subst in db.ask(equal(X, 2), equal(Y, 3), let(R, X * Y + 1)):
...     print(subst[R])  # R is X * Y + 1
...
7
```

Supported arithmetic operators: `+ - * / // % ** ~ & | ^ << >>`

---

## Definite Clause Grammars (DCGs)

Hornet supports DCG notation via `DCG()` and `DCGs()`:

```python
from hornet import DCGs, database
from hornet.symbols import s, np, vp, noun, verb, det, phrase

db = database()
db.tell(*DCGs(
    s.when(np, vp),
    np.when(det, noun),
    vp.when(verb),
    det.when(['the']),
    noun.when(['cat']),
    verb.when(['sleeps']),
))

for subst in db.ask(phrase(s, ['the', 'cat', 'sleeps'])):
    print('parsed!')
```

DCG rules are automatically expanded to difference lists. The `inline(goal)` escape hatch lets you embed regular goals inside a DCG body.

---


## Extending with Python

Register native Python predicates using the `@predicate` decorator. This is how `ifelse/3` is implemented internally:

```python
from hornet import database, predicate
from hornet.clauses import Database, Environment, Subst
from hornet.combinators import Step, if_then_else
from hornet.clauses import resolve
from hornet.symbols import ifelse, T, Y, N

db = database()

@db.tell
@predicate(ifelse(T, Y, N))
def _(db: Database, subst: Subst) -> Step[Database, Environment]:
    return if_then_else(
        resolve(subst[T]),
        resolve(subst[Y]),
        resolve(subst[N]),
    )(db, subst.env)
```

---

## Architecture

Hornet is built on two main layers:

**Term algebra** (`hornet.terms`): Python expressions construct expression trees rather than computing values. Operator overloading (`+`, `*`, `|`, `**`, …) and `__call__` produce nested `Symbolic` structures — `Functor`, `Atom`, `Variable`, `Cons`, `Operator` subclasses — which represent both data and goals. `promote()` lifts Python primitives (integers, strings, lists) into this algebra transparently. Technically the term algebra is free over a set of variables.

**Resolution engine** (`hornet.combinators`): A *triple-barrelled continuation monad* drives search. Every goal is a function `(ctx, subst) → Step`, where a `Step` takes three continuations — *success* (emit a substitution and continue), *failure* (backtrack), and *prune* (implement cut). The combinators `then`, `choice`, `prunable`, `neg`, and `if_then_else` compose goals; `trampoline()` drives the whole thing iteratively to avoid stack overflow.

---

## Examples

The `examples/` directory includes:

- `append.py` — list concatenation (forward) and splitting (backward) via backtracking
- `queens.py` — N-queens constraint solver
- `fizzbuzz.py` — FizzBuzz via DCGs
- `symdiff.py` — symbolic differentiation and simplification
- `parsing.py` — natural language parsing with a German grammar
- `turing.py` — a Turing machine interpreter
- `hanoi.py` — Towers of Hanoi with Turtle graphics (requires `tkinter`)

### FizzBuzz via DCGs

A concise demonstration of DCG notation, arithmetic, and backtracking working together:

```python
from toolz import take

from hornet import DCGs, database
from hornet.clauses import Database
from hornet.symbols import (
    M, N, R, S, V, Ws, _,
    cut, equal, fb, fizzbuzz, ifelse, inline,
    join, let, phrase, word, words,
)


def main(db: Database):
    db.tell(
        fizzbuzz(R).when(
            fb(1, R),
        ),
        fb(N, R).when(
            phrase(words(N), Ws),
            join(Ws, S),
            ifelse(
                equal(S, ''),
                equal(N, R),
                equal(S, R),
            ),
        ),
        fb(N, R).when(
            let(M, N + 1),
            fb(M, R),
        ),
        *DCGs(
            words(N).when(
                word(3, N),
                word(5, N),
                word(7, N),
                inline(cut),
            ),
            word(3, N).when(inline(let(M, N % 3), equal(M, 0)), ['fizz']),
            word(5, N).when(inline(let(M, N % 5), equal(M, 0)), ['buzz']),
            word(7, N).when(inline(let(M, N % 7), equal(M, 0)), ['quux']),
            word(_, _),
        ),
    )

    for s in take(1111, db.ask(fizzbuzz(V))):
        print(s[V])


if __name__ == '__main__':
    main(database())
```

---

## Documentation

* [API Documentation](docs/API.md)
* [Glossary](docs/Glossary.md)

---

## Links

### Horn Clauses
https://en.wikipedia.org/wiki/Horn_clause

### Logical Resolution
http://web.cse.ohio-state.edu/~stiff.4/cse3521/logical-resolution.html

### Unification
https://eli.thegreenplace.net/2018/unification/

### Backtracking
https://en.wikipedia.org/wiki/Backtracking

### Monoids
https://en.wikipedia.org/wiki/Monoid

### Folding on Monoids
https://bartoszmilewski.com/2020/06/15/monoidal-catamorphisms/

### Distributive Lattices
https://en.wikipedia.org/wiki/Distributive_lattice

### Monads
https://en.wikipedia.org/wiki/Monad_(functional_programming)

### Continuations
https://en.wikipedia.org/wiki/Continuation

### Continuations Made Simple and Illustrated
https://www.ps.uni-saarland.de/~duchier/python/continuations.html

### The Discovery of Continuations
https://www.cs.ru.nl/~freek/courses/tt-2011/papers/cps/histcont.pdf

### Tail Calls
https://en.wikipedia.org/wiki/Tail_call

### On Recursion, Continuations and Trampolines
https://eli.thegreenplace.net/2017/on-recursion-continuations-and-trampolines/

---

## License

MIT.
