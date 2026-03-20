
# Hornet Architecture

## Overview

Hornet is an embedded domain-specific language (EDSL) for logic programming in Python. It combines:

- a **pure logic fragment** (Horn clauses over a free term algebra)
- a **sequential control algebra** (composable execution semantics)

This design separates *what is true* (logic) from *how it is computed* (control), and makes control a first-class, compositional structure rather than an implicit operational mechanism.

---

## Core Components

### 1. Free Term Algebra

Hornet represents all logic expressions as elements of a **free term algebra**. Terms are constructed from:

- **Atoms** (constants)
- **Variables**
- **Functors** (n-ary constructors)

Python syntax is overloaded so that expressions build *symbolic structures* rather than compute values.

**Example:**

```python
f(X, g(Y, 3))
```

This produces a tree:

```
    f
   / \
  X   g
     / \
    Y   3
```

**Key properties:**

- Terms are purely syntactic
- No equations hold a priori
- Equality is structural
- Unification computes substitutions that make terms equal

This differs from standard algebras, where equations like commutativity are built in.

---

### 2. Horn Clauses

Hornet uses Horn clauses as its logical core.

**Forms:**

- Fact: `p(a)`
- Rule: `q(X) :- p(X)`
- Query: `?- q(X)`

**In Hornet:**

```python
db.tell(human('socrates'))
db.tell(mortal(X).when(human(X)))

for subst in db.ask(mortal(X)):
    print(subst[X])
```

**Characteristics:**

- Implicit quantification (no explicit ∀ / ∃)
- Restricted but expressive fragment of first-order logic
- Enables efficient operational semantics

---

### 3. Unification

Unification is the process of finding a substitution σ such that:

```
σ(t₁) = σ(t₂)
```

**Example:**

```
f(X, 3)  ~  f(2, Y)
⇒ σ = { X ↦ 2, Y ↦ 3 }
```

**Hornet implements:**

- Structural recursion
- Dereferencing of variables with path compression
- Cycle detection

The result is a substitution — a mapping from variables to terms, represented as an immutable `Map[Variable, Term]` (the `Environment` type).

---

### 4. Resolution (SLD-Resolution)

Hornet evaluates queries using SLD-resolution:

1. Select a goal
2. Find a clause whose head unifies with it
3. Replace the goal with the clause body
4. Continue recursively

**Search strategy:**

- Depth-first
- Left-to-right
- Backtracking over alternatives

This is not arbitrary search, but a goal-directed linear resolution strategy.

---

### 5. The `resolve()` Functor

`resolve()` is the architectural hinge between the two layers of Hornet. It is a functor from the term category into the combinator category:

```
resolve : Term → Goal[Database, Environment]
```

It translates symbolic term structure — atoms, functors, `AllOf`, `AnyOf`, `Invert` — into executable combinator expressions. Because this translation is explicit and isolated, the resolution engine is swappable without touching the term algebra, and the term algebra is constructable without knowing anything about execution.

**This boundary is what makes Hornet extensible.** Adding new logical connectives means extending `resolve()`; modifying the search strategy means replacing combinators. Neither requires changes to the other layer.

---

## Control Algebra

### 6. Goals and Execution Model

A goal is a function:

```
Goal : (Database, Environment) → Step
```

A step is a computation in continuation-passing style:

```
Step : (yes, no, prune) → Result
```

Where:

- `yes` — success continuation: propagates the result `Environment` forward
- `no` — failure continuation: backtracks to the last choice point
- `prune` — cut continuation: commits past the last choice point

Execution proceeds by repeatedly invoking steps via a trampoline (see below).

---

### 7. Sequential Control Algebra

Hornet's resolution combinators form a **sequential control algebra**.

#### Sequential Composition

```
then(A, B)
```

*Execute A, then continue with B using the resulting substitution.*

Identity: `unit`

```
then(A, unit) = A
then(unit, A) = A
```

#### Non-Deterministic Choice

```
choice(A, B)
```

*Try A; if it fails, try B.*

Identity: `fail`

```
choice(A, fail) = A
choice(fail, A) = A
```

---

### 8. Algebraic Perspective

The combinators induce a structured control algebra:

- `(then, unit)` forms a **monoid** (sequential composition)
- `(choice, fail)` forms a **monoid** (non-deterministic choice)

**This algebra is deliberately non-commutative and non-distributive.** `then` is not commutative because order of execution matters. Distributivity of sequencing over choice — `then(A, choice(B, C)) = choice(then(A, B), then(A, C))` — fails in the presence of cut, which can redirect control inside `B` or `C` in ways that break the equation. This is not a deficiency; it reflects the real semantics of sequential search with pruning. The non-commutativity and non-distributivity are load-bearing.

---

### 9. Cut as First-Class Control

Traditional Prolog treats cut as an operational hack that breaks the declarative reading. Hornet inverts this perspective:

> **Cut is a first-class element of the control algebra.**

**Operationally:**

- Cut redirects control from `no` to `prune`
- It commits to the current branch
- It discards alternative choices up to a defined boundary

**The boundary is explicit.** Cut only prunes within a `prunable` scope. A `prunable` context sets `prune = no` for its inner computation, so cut inside a `prunable` block jumps to the enclosing `no` rather than escaping globally. This is what prevents cut from being a global control hack and preserves composability: you can reason about cut locally.

**Conceptually:**

- Cut is not outside the model
- It is an algebraic operation over continuations
- Its scope is governed by `prunable`, not by implicit call stack position

---

## Continuation-Passing Semantics

### 10. Triple Continuation Model

Hornet uses a three-continuation CPS encoding:

| Continuation | Role |
|---|---|
| `yes` | Propagate success, carrying the updated `Environment` |
| `no` | Perform backtracking to the last choice point |
| `prune` | Implement cut — commit past the last choice point |

**This allows:**

- Non-determinism
- Structured backtracking
- Early exit and scoped pruning

All control flow is expressed through these continuations. There are no hidden control effects.

---

### 11. Trampolining

To avoid stack overflow in deep searches, Hornet uses a trampoline:

- Computations return thunks (deferred steps) rather than calling continuations directly
- An outer loop executes them iteratively

**This provides:**

- Stack safety for deep or infinite search spaces
- Predictable memory usage
- No dependency on Python's recursion limit

---

## Separation of Concerns

Hornet enforces a strict separation:

| Layer | Responsibility |
|---|---|
| Logic | Facts, rules, unification, term structure |
| Control | Sequencing, choice, cut, search strategy |

The `resolve()` functor is the explicit, narrow interface between them.

---

## Modal Extension *(In Progress)*

Hornet's database is a `ChainMap` — child databases are created cheaply via `new_child()`, inheriting all parent clauses while allowing local additions that do not affect the parent. This makes the database a natural representation of a *possible world*: branching, versioning, and scoped extension come for free.

The modal extension makes this explicit:

```
Goal : (World, Environment) → Step
```

Modal operators are interpreted as quantification over worlds with respect to an accessibility relation R:

- **Necessity:** ∀w ∈ R(current): p(w)
- **Possibility:** ∃w ∈ R(current): p(w)
- **Impossibility:** ¬∃w ∈ R(current): p(w)

**This enables three combined modalities:**

- **Temporal** — time-indexed worlds; rules and facts carry timestamps; queries respect which version of a ruleset was in force at the time of an event
- **Epistemic** — knowledge of agents; what did an agent know, and when?
- **Deontic** — obligations and norms; what should an agent have done, known, or refrained from?

Worlds can be extended, branched, or versioned. The `ChainMap` structure means none of this requires special machinery — it is already in the design.

---

## Design Summary

Hornet integrates:

- A free term algebra for symbolic structure
- Horn clauses for logic
- Unification + SLD-resolution for inference
- A `resolve()` functor as the explicit boundary between logic and control
- A sequential control algebra for execution
- A multi-continuation CPS model for control flow
- A `ChainMap`-based database that naturally supports possible-worlds semantics

The result is a system where logic is pure, control is explicit, and both compose cleanly.

---

## Key Insight

Hornet reverses the traditional view of logic programming:

> Control is not an implementation detail of logic.
> It is an algebra in its own right.

And:

> Cut is not an embarrassment.
> It is a primitive of that algebra — one whose scope is governed by `prunable`, not by convention.
