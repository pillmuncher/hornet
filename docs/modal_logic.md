# Modal Logic in Hornet

## Overview

`hornet.modalities` extends Hornet with **constructive modal logic**. Rather than
treating possible worlds as a background relation (in the classical Kripke sense),
Hornet *generates* worlds by systematically transforming a root `Database`. Modal
truth is then defined by quantification over those generated worlds.

Two modalities are built in:

| Modality | Direction | Mechanism |
|---|---|---|
| **Epistemic** | Restriction ↓ | Shadow subsets of accessible facts |
| **Deontic** | Extension ↑ | Overlay subsets of performed obligations |

Because worlds are constructed from the live database, they inherit all existing
facts and rules, and Hornet's normal resolution engine handles all inference within
each world.

---

## Core Concepts

### Worlds as Database Variants

A *world* is simply a `Database` — a `ChainMap` layer over the root knowledge base.
`Database.shadow(*terms)` creates a child in which selected facts are overridden to
fail (information removal), while `Database.overlay(*terms)` creates a child in
which additional facts are asserted (information addition).

```
root DB
  │
  ├─ shadow(fact_A.when(fail))   → world without fact_A  (epistemic restriction)
  └─ overlay(performed(A, act))  → world with act performed  (deontic extension)
```

### World Generators

A **world generator** is a callable `Database → tuple[Database, ...]`. It receives
the current database and returns the set of alternative worlds to quantify over.
The `powerset` utility enumerates all subsets of a collection, so `n` accessible
facts or obligations yield exactly `2ⁿ` worlds (the empty subset is always included,
preserving reflexivity — Axiom T).

### Quantifiers

```
□φ  ≡  forall(generator, φ)   # φ holds in all generated worlds
◇φ  ≡  exists(generator, φ)   # φ holds in some generated world
```

These compose cleanly. Nesting them gives combined modalities:

| Expression | Reading |
|---|---|
| `forall(deontic, exists(epistemic, φ))` | For every obligation scenario, there is some epistemic state in which φ holds |
| `forall(epistemic, exists(deontic, φ))` | In every epistemic state, some duty makes φ hold |
| `exists(deontic, forall(epistemic, φ))` | Some duty guarantees φ regardless of what is known |
| `forall(deontic, forall(epistemic, φ))` | φ holds in every knowledge-obligation combination |

Because `forall(A, forall(B, φ)) ≡ forall(B, forall(A, φ))` and similarly for
`exists`, pure same-type nesting commutes; mixed nesting generally does not.

---

## API Reference

### `modal(db: Database) → Database`

Wraps a database with the four standard modal predicates (`k`, `o`, `possibly_k`,
`possibly_o`). Returns a new child database that inherits everything from `db` and
additionally understands those predicates.

```python
from hornet import database
from hornet.modalities import modal

db = modal(database())
```

---

### `k(Query, Agent, T)`

**Necessity — epistemic.** Succeeds if `Query` is provable in *all* epistemic worlds
accessible to `Agent` at time `T` (i.e. in all possible bounded-awareness variants
of the current database).

```python
for s in db.ask(k(report_accurate, 'alice', 3)):
    print('Alice necessarily knows this')
```

Defined as `forall(epistemic_worlds(Agent, T), resolve(Query))`.

---

### `possibly_k(Query, Agent, T)`

**Possibility — epistemic.** Succeeds if `Query` is provable in *some* epistemic
world accessible to `Agent` at time `T`.

```python
for s in db.ask(possibly_k(fact, 'alice', 3)):
    print('Alice could know this')
```

Defined as `exists(epistemic_worlds(Agent, T), resolve(Query))`.

---

### `o(Query, Agent, T)`

**Necessity — deontic.** Succeeds if `Query` holds in *all* deontic worlds for
`Agent` at time `T` (i.e. under every possible pattern of obligation fulfillment).

Defined as `forall(deontic_worlds(Agent, T), resolve(Query))`.

---

### `possibly_o(Query, Agent, T)`

**Possibility — deontic.** Succeeds if `Query` holds in *some* deontic world for
`Agent` at time `T`.

Defined as `exists(deontic_worlds(Agent, T), resolve(Query))`.

---

### `epistemic_worlds(agent, t) → WorldGenerator`

Returns a world generator that, when called with a database, queries
`accessible(agent, Fact, t)` for all bound facts and produces one world per subset
of those facts by shadowing the hidden ones with `fact.when(fail)`.

```python
worlds = epistemic_worlds('alice', 3)(db)   # tuple of Database variants
```

For `n` accessible facts this yields exactly `2ⁿ` worlds. The empty-hidden-set
world is the base database itself (reflexivity).

---

### `deontic_worlds(agent, t) → WorldGenerator`

Returns a world generator that queries `obligation(agent, Action, t)` and produces
one world per subset of those obligations by overlaying `performed(agent, act, t)`
for each fulfilled subset.

```python
worlds = deontic_worlds('alice', 3)(db)
```

Again, `2ⁿ` worlds for `n` obligations. The empty subset represents no obligations
being fulfilled; the full subset represents all of them being fulfilled.

---

### `exists(generator, query) → Goal`

Succeeds if `query` holds in at least one world produced by `generator`.
Implemented as `then(Branch(generator), query)`.

---

### `forall(generator, query) → Goal`

Succeeds if `query` holds in every world produced by `generator`. Implemented via
double negation: `neg(then(Branch(generator), neg(query)))`. Vacuously true when
the generator produces zero worlds.

---

### `powerset(iterable) → tuple[tuple, ...]`

Returns all subsets of `iterable` as a tuple of tuples (including the empty set and
the full set). Used internally by `epistemic_worlds` and `deontic_worlds`.

```python
powerset([1, 2])
# → ((), (1,), (2,), (1, 2))
```

---

### `Branch(generator)`

A callable dataclass that turns a `WorldGenerator` into a `Goal`. When resolved, it
branches the search into one alternative per generated world, switching the current
database context to each in turn. This is the primitive over which `exists` and
`forall` are built.

---

## Extending with Custom Modalities

You can define additional predicates on top of the generated worlds using the
standard `@predicate` decorator. The compliance example below demonstrates how to
combine deontic and epistemic quantifiers into a single `deemed_known` predicate
that encodes a legal notion of constructive knowledge.

### Defining `deemed_known` — the `∀ₒ∃ₖ` pattern

The predicate `deemed_known(Agent, Fact, T)` captures the legal idea that an agent
is *deemed to know* a fact if, in every possible world where they fulfil their
obligations, there exists some epistemic state in which they have access to that
fact. This is the `∀ₒ (∃ₖ accessible(...))` pattern.

```python
from hornet import database
from hornet.clauses import Database, Environment, Subst, predicate, resolve
from hornet.combinators import Step
from hornet.modalities import deontic_worlds, epistemic_worlds, exists, forall, modal
from hornet.symbols import Agent, Fact, T, accessible, deemed_known


def compliance(db: Database) -> Database:
    child = modal(db.new_child())

    @child.tell
    @predicate(deemed_known(Agent, Fact, T))
    def _(db: Database, subst: Subst) -> Step[Database, Environment]:
        return forall(
            deontic_worlds(subst[Agent], subst[T]),
            exists(
                epistemic_worlds(subst[Agent], subst[T]),
                resolve(accessible(subst[Agent], subst[Fact], subst[T])),
            ),
        )(db, subst.env)

    return child
```

The predicate body receives the bound values of `Agent`, `Fact`, and `T` from the
substitution and constructs a nested quantifier expression on the fly. Note that
`subst[Agent]` dereferences the logical variable to its ground value before passing
it into the world generators, which expect concrete Python values (strings, atoms,
etc.).

---

## Full Example — Compliance Audit

The following scenario shows how to combine Event Calculus rules (built into Hornet)
with modal operators to answer the question: *"Is Alice legally deemed to know about
a regulatory violation?"*

### Domain setup

```python
from hornet import database
from hornet.modalities import deontic_worlds, epistemic_worlds, exists, forall, modal
from hornet.symbols import (
    TX, Agent, Amount, Fact, Limit, Regulation, Report, Role,
    T, T_report, Tmax, _,
    accessible, after, appointed, deemed_known, enacted, greater,
    happens_at, holds_at, initiates, mentions, obligation,
    published, review, threshold, transaction, violated, violation,
)
```

### Building the knowledge base

```python
db = compliance(database())

db.tell(
    # Timeline of events (Event Calculus: happens_at/2)
    happens_at(enacted('reg31'), 0),           # Regulation enacted
    happens_at(appointed('alice', 'cfo'), 1),  # Alice becomes CFO
    happens_at(transaction('tx17', 'bob', 250_000), 2),  # Transaction occurs
    happens_at(published('rep42'), 3),          # Report published

    # Static facts
    threshold('reg31', 100_000),   # Regulation sets a 100k threshold
    mentions('rep42', 'tx17'),     # Report mentions the transaction

    # Causal rules (Event Calculus: initiates/2)
    initiates(enacted(Regulation), in_force(Regulation)),
    initiates(appointed(Agent, Role), tenure(Agent, Role)),

    # A transaction violates a regulation if the amount exceeds the threshold
    # while the regulation is in force
    violation(TX, Regulation).when(
        happens_at(transaction(TX, _, Amount), T),
        holds_at(in_force(Regulation), T),
        threshold(Regulation, Limit),
        greater(Amount, Limit),
    ),

    # Accessibility rules: what facts can an agent access?
    accessible(Agent, violated(TX, Regulation), Tmax).when(
        accessible(Agent, transaction(TX, Amount), Tmax),
        violation(TX, Regulation),
    ),
    accessible(Agent, transaction(TX, Amount), Tmax).when(
        mentions(Report, TX),
        happens_at(published(Report), T_report),
        ~after(T_report, Tmax),
        holds_at(tenure(Agent, 'cfo'), Tmax),
    ),

    # Obligation rules: what must an agent do?
    obligation(Agent, review(Report), T_report).when(
        happens_at(published(Report), T_report),
        holds_at(tenure(Agent, 'cfo'), T_report),
    ),
)
```

Alice never actually reviews `rep42` — the `happens_at(performed('alice', review('rep42'), _))`
fact is intentionally absent. The question is whether she is *deemed* to know the
violation anyway.

### Querying

```python
query = deemed_known('alice', violated('tx17', 'reg31'), 3)
result = any(db.ask(query))
print(f'Liability Check: {query} -> {result}')
```

The resolution proceeds as follows:

1. `deemed_known` triggers the `∀ₒ∃ₖ` predicate body.
2. `deontic_worlds` finds Alice's obligations at time 3 (review `rep42`) and
   generates two worlds: one in which she performed the review, and one in which she
   did not.
3. For each deontic world, `epistemic_worlds` generates all sub-theories by
   shadowing subsets of accessible facts.
4. `exists` checks whether the violation is accessible in at least one of those
   epistemic worlds.
5. `forall` requires this to hold across all deontic worlds.

In the world where Alice performs the review, she gains access to the transaction
record and therefore to the violation — so `deemed_known` succeeds.

### Side note: Event Calculus (Brief Overview)

The audit example uses a lightweight Event Calculus to separate *what happens* from *what holds over time*. Facts of the form `happens_at(...)` describe discrete events (e.g. appointments, transactions, publications), while fluents such as roles or regulations in force are derived via `initiates` and queried using `holds_at`. Fluents persist by default: once initiated, they continue to hold unless terminated. Derived predicates (e.g. `violation`, `accessible`, `obligation`) are defined declaratively in terms of both events and fluents, allowing the system to reconstruct the relevant state at any time point. This separation keeps the temporal structure explicit while supporting causal and legal-style reasoning within the modal framework.

---

## Design Notes

### Accessibility is generative, not relational

Classical Kripke semantics defines accessibility as a binary relation `R(w₁, w₂)`
between worlds. Hornet instead treats it as a *generator* — a function that
constructs the set of alternative worlds from the current database. This keeps
worlds concrete (they are real databases, not abstract nodes) and makes the
accessibility structure programmable in ordinary Python.

### Asymmetry of the two modalities

Epistemic worlds are produced by *removing* information (shadowing facts to fail),
which is a non-monotone operation: a fact that was provable may become unprovable.
Deontic worlds are produced by *adding* information (overlaying performed actions),
which is monotone: once something is asserted, it stays true in that world.

This asymmetry is deliberate and reflects the underlying logic: knowledge is bounded
by what evidence is available, while obligation fulfillment is an additive notion —
you can only do more, not less, than the base case.

### Reflexivity (Axiom T) comes for free

Because `powerset` always includes the empty subset, the base database is always one
of the generated worlds. This means that if a formula is modally true (holds in all
worlds), it is in particular true in the base world — which is exactly Axiom T
(`□φ → φ`).

### Integration with Hornet's control algebra

`Branch`, `exists`, and `forall` are ordinary `Goal`-valued functions and compose
with the rest of Hornet's combinator library (`then`, `neg`, `prunable`, etc.)
without any special cases. Cut, negation-as-failure, and backtracking all work
normally within and across modal worlds.
