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
    human('socrates'),                     # fact
    mortal(X).when(human(X)),             # rule: mortal(X) :- human(X).
)
```

### Queries

```python
from hornet import database
from hornet.symbols import X, mortal

db = database()
db.tell(human('socrates'))
db.tell(mortal(X).when(human(X)))

for subst in db.ask(mortal(X)):
    print(subst[X])   # → socrates
```

`db.ask()` returns an iterable of substitutions. Each substitution maps variables to their bound values.

---

## Built-in Predicates

Hornet ships a standard library of predicates pre-loaded in every database:

| Predicate | Description |
|---|---|
| `equal(X, Y)` | Unification (`X = Y`) |
| `unequal(X, Y)` | Negation of unification |
| `let(R, Expr)` | Arithmetic evaluation (`R is Expr`) |
| `arithmetic_equal(X, Y)` | Arithmetic equality |
| `smaller(A, B)` / `greater(A, B)` | Numeric comparison |
| `call(G)` | Call a goal term |
| `once(G)` | Call G, commit to first solution |
| `findall(O, G, L)` | Collect all solutions |
| `member(X, L)` | List membership |
| `append(A, B, C)` | List concatenation |
| `reverse(L, R)` | List reversal |
| `select(X, L, R)` | Select element from list |
| `length(L, N)` | List length |
| `maplist(G, L)` | Apply goal to each list element |
| `is_var`, `nonvar`, `is_atom`, `is_int`, … | Type checks |
| `write`, `writeln`, `nl` | I/O |
| `cut` | Prolog cut (`!`) |
| `fail` | Always fails |
| `true` | Always succeeds |
| `repeat` | Succeeds infinitely |
| `throw(E)` | Raise an exception |
| `ifelse(T, Y, N)` | Soft-cut conditional |
| `phrase(G, L)` | DCG query |

---

## Arithmetic

Arithmetic expressions are built using Python's operators on symbolic terms and evaluated lazily by `let`:

```python
from hornet.symbols import X, Y, R, let, arithmetic_equal

# R is X * Y + 1
db.ask(let(R, X * Y + 1))

# supported: + - * / // % ** ~ & | ^ << >>
```

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

DCG rules are automatically expanded to difference lists. The `inline(goal)` escape hatch lets you embed regular Prolog goals inside a DCG body.

---

## Extending with Python

Register native Python predicates using the `@predicate` decorator. This is how `ifelse/3` is implemented internally:

```python
from hornet import database, predicate
from hornet.clauses import Database, Environment, Subst
from hornet.combinators import Step, if_then_else
from hornet.clauses import resolve
from hornet.symbols import T, Y, N

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

**Term algebra** (`hornet.terms`): Python expressions construct expression trees rather than computing values. Operator overloading (`+`, `*`, `|`, `**`, …) and `__call__` produce nested `Symbolic` structures — `Functor`, `Atom`, `Variable`, `Cons`, `Operator` subclasses — which represent both data and goals. `promote()` lifts Python primitives (integers, strings, lists) into this algebra transparently.

**Resolution engine** (`hornet.combinators`): A *triple-barrelled continuation monad* drives search. Every goal is a function `(ctx, subst) → Step`, where a `Step` takes three continuations — *success* (emit a substitution and continue), *failure* (backtrack), and *prune* (implement cut). The combinators `then`, `choice`, `prunable`, `neg`, and `if_then_else` compose goals; `trampoline()` drives the whole thing iteratively to avoid stack overflow.

---

## Examples

The `examples/` directory includes:

- `append.py` — list splitting via backtracking
- `queens.py` — N-queens constraint solver
- `fizzbuzz.py` — FizzBuzz via DCGs
- `symdiff.py` — symbolic differentiation and simplification
- `parsing.py` — natural language parsing with a German grammar
- `turing.py` — a Turing machine interpreter
- `hanoi.py` — Towers of Hanoi with Turtle graphics

---

## License

MIT. See `LICENSE.md`.
