# API Documentation

## Term Types

```python
from hornet.terms import Variable
Variable(name: str)
```

* Represents a named logical variable. Names beginning with an uppercase letter
  or `_` are automatically created as `Variable`s when accessed via
  `hornet.symbols`. The anonymous wildcard `_` matches anything and is never
  bound.

---

```python
from hornet.terms import Atom
Atom(name: str)
```

* Represents a symbolic constant or zero-arity predicate head. Lowercase names
  accessed via `hornet.symbols` are automatically `Atom`s. Calling an `Atom`
  with arguments produces a `Functor`.

---

```python
from hornet.terms import Functor
Functor(name: str, *args: Term)
```

* Represents a compound term — a named relation applied to one or more
  arguments. Produced by calling an `Atom`: `parent(X, Y)` yields
  `Functor('parent', Variable('X'), Variable('Y'))`.

---

```python
from hornet.terms import Cons, Empty
```

* `Cons(head, tail)` is the list cell. `Empty` is the nil terminator `[]`.
  Python lists are automatically promoted to `Cons` chains by `promote()`.
  The `|` operator on a symbolic term creates a `Cons` with a variable tail:
  `[H | T]`.

---

```python
from hornet.terms import promote
promote(obj: Any) -> Term
```

* Lifts Python values into the term algebra. Integers, floats, strings, bools,
  bytes, and complex numbers pass through unchanged. Python lists become `Cons`
  chains. Tuples are promoted element-wise. `Functor` and `Operator` arguments
  are promoted recursively.

---

```python
from hornet.terms import HornetRule
term.when(*goals: Term | list) -> HornetRule
```

* Constructs a Horn clause. The receiver is the head; the arguments are the
  body goals, interpreted as conjunction. A bare list in the body is treated
  as a DCG terminal sequence (inside `DCGs()`).

---

```python
from hornet.terms import DCG, DCGs
DCG(rule: HornetRule | Atom | Functor) -> HornetRule | Functor
DCGs(*rules) -> tuple[HornetRule | Functor, ...]
```

* Expands DCG notation to ordinary Horn clauses by threading difference-list
  state variables through each goal. Use `DCGs()` to expand multiple rules at
  once and splat the result into `db.tell()`. The `inline(goal)` escape hatch
  embeds a regular goal inside a DCG body without threading state through it.

---

## Database

```python
from hornet import database
database() -> Database
```

* Returns a new `Database` that inherits all built-in predicates. Each call
  produces an independent child; asserting facts into it does not affect the
  parent.

---

```python
db.new_child() -> Database
```

* Returns a new `Database` layered on top of `db`. Facts asserted into the
  child are visible there but not in the parent, enabling scoped or temporary
  extensions of a knowledge base.

---

```python
db.tell(*terms: NonVariable) -> None
```

* Asserts one or more facts or rules into the database. Terms are processed in
  order; each is compiled to an internal `Clause` and indexed by its predicate
  indicator `(name, arity)`. Can also be used as a decorator (see
  `@predicate`).

---

```python
db.ask(*goals: NonVariable, subst: Subst | None = None) -> Iterable[Subst]
```

* Runs a conjunctive query and returns a lazy iterable of substitutions, one
  per solution. Variables in the goals are renamed before resolution so
  repeated calls are independent. An optional initial `subst` seeds the
  environment.

---

```python
from hornet.clauses import Subst
subst[variable] -> Term
```

* Dereferences a variable in a substitution returned by `db.ask()`. Chains of
  variable bindings are followed to their ground value.

---

## Extending with Python

```python
from hornet.clauses import predicate
@db.tell
@predicate(head_term)
def _(db: Database, subst: Subst) -> Step[Database, Environment]:
    ...
```

* Registers a native Python function as the body of a Horn clause whose head
  is `head_term`. The function receives the current database and substitution
  and must return a `Step` — typically `unit(db, subst.env)` to succeed,
  `fail(db, subst.env)` to fail, or a combinator expression. Variables in
  `head_term` are accessible in `subst` after unification.

---

## Built-in Predicates

### Logic and Control

```python
true
```
* Always succeeds.

---

```python
fail
```
* Always fails. Triggers backtracking.

---

```python
cut
```
* Succeeds once, then prunes remaining choice points in the current `prunable`
  context — equivalent to Prolog's `!`.

---

```python
repeat
```
* Succeeds infinitely on backtracking.

---

```python
call(G)
```
* Resolves the term `G` as a goal. Equivalent to Prolog's `call/1`.

---

```python
once(G)
```
* Calls `G` and commits to its first solution, discarding further alternatives.

---

```python
ignore(G)
```
* Calls `G` but always succeeds, regardless of whether `G` succeeds or fails.

---

```python
ifelse(T, Y, N)
```
* Soft-cut conditional. If `T` succeeds, commits to `Y` (does not try `N`).
  If `T` fails, executes `N`. Unlike `(T -> Y ; N)` in standard Prolog, all
  solutions of `Y` are explored when `T` succeeds.

---

```python
throw(E)
```
* Raises `E` as a Python exception, unwinding the resolution stack.

---

### Negation

```python
~goal
```
* Negation-as-failure. Succeeds if `goal` fails; fails if `goal` succeeds.
  No bindings made during the test escape. Implemented via the `Invert`
  operator on any symbolic term, expanding to `neg(resolve(goal))` at
  resolution time.

---

### Unification

```python
equal(X, Y)
```
* Unifies `X` and `Y`. Succeeds if they can be made identical under the
  current substitution; binds variables as a side-effect. Equivalent to
  Prolog's `=/2`.

---

```python
unequal(X, Y)
```
* Succeeds if `X` and `Y` cannot be unified. Defined as `~equal(X, Y)`.
  No bindings escape.

---

```python
univ(T, L)
```
* Relates a term to its functor-name-and-arguments list, like Prolog's `=../2`
  ("univ"). If `T` is bound, `L` is unified with `[name | args]`. If `T` is
  unbound and `L` is bound, `T` is constructed from `L`.

---

### Arithmetic

```python
let(R, Expr)
```
* Evaluates the arithmetic expression `Expr` and unifies the result with `R`.
  Equivalent to Prolog's `is/2`. Operators `+ - * / // % ** ~ & | ^ << >>`
  are all supported on symbolic terms and evaluated lazily here.

---

```python
arithmetic_equal(X, Y)
```
* Evaluates both `X` and `Y` as arithmetic expressions and unifies the
  results. Succeeds iff they are numerically equal.

---

```python
smaller(A, B)
```
* Succeeds if the numeric value of `A` is strictly less than that of `B`.

---

```python
greater(A, B)
```
* Succeeds if the numeric value of `A` is strictly greater than that of `B`.

---

### Lists

```python
append(A, B, C)
```
* True when list `C` is the concatenation of lists `A` and `B`. Works in all
  directions: given any two, the third can be derived via backtracking.

---

```python
member(X, L)
```
* Succeeds for each element of list `L` that unifies with `X`. Enumerates on
  backtracking.

---

```python
select(X, L, R)
```
* Succeeds when `X` is an element of `L` and `R` is `L` with one occurrence
  of `X` removed. Enumerates on backtracking.

---

```python
reverse(L, R)
```
* Unifies `R` with the reverse of list `L`.

---

```python
length(L, N)
```
* Unifies `N` with the number of elements in list `L`.

---

```python
maplist(G, L)
```
* Calls `G` on each element of list `L` in turn. Succeeds iff all calls
  succeed. `G` is applied via `univ` so that `G` is treated as a partial
  functor applied to each element.

---

```python
findall(O, G, L)
```
* Collects all bindings of `O` produced by solutions to `G` into the list `L`.
  Never fails; `L` is `[]` if `G` has no solutions. `O` must be an unbound
  variable at call time.

---

### String / Term I/O

```python
join(L, S)
```
* Unifies `S` with the string formed by concatenating all string elements of
  list `L`.

---

```python
write(V)
```
* Prints the value of `V` without a trailing newline.

---

```python
writeln(V)
```
* Prints the value of `V` followed by a newline.

---

```python
nl
```
* Prints a newline. Defined as `writeln('')`.

---

```python
lwriteln(L)
```
* Prints each element of list `L` on its own line.

---

### DCG

```python
phrase(G, L)
```
* Runs DCG goal `G` against token list `L`. Equivalent to calling the
  difference-list expanded form of `G` with `L` and `[]` as the state
  arguments.

---

### Type Checks

All type-check predicates succeed if the argument satisfies the test and fail
otherwise. None bind any variables.

| Predicate      | Python equivalent             |
|----------------|-------------------------------|
| `is_var(V)`    | `isinstance(V, Variable)`     |
| `nonvar(V)`    | `not isinstance(V, Variable)` |
| `is_atom(V)`   | `isinstance(V, Atom)`         |
| `is_atomic(V)` | `isinstance(V, Atom \| str \| int \| float \| bool \| bytes \| complex)` |
| `is_constant(V)` | same as `is_atomic`         |
| `is_int(V)`    | `isinstance(V, int)`          |
| `is_float(V)`  | `isinstance(V, float)`        |
| `is_numeric(V)`| `isinstance(V, numbers.Number)` |
| `is_bool(V)`   | `isinstance(V, bool)`         |
| `is_str(V)`    | `isinstance(V, str)`          |
| `is_bytes(V)`  | `isinstance(V, bytes)`        |
| `is_complex(V)`| `isinstance(V, complex)`      |
