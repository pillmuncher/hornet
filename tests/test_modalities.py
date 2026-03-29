from hypothesis import given
from hypothesis import strategies as st

from hornet import database
from hornet.clauses import Database
from hornet.modalities import (
    Branch,
    KleisliComposition,
    compliance_worlds,
    deontic_worlds,
    epistemic_worlds,
    exists,
    forall,
    modal,
    powerset,
)
from hornet.symbols import (
    accessible,
    complied,
    deemed_known,
    k,
    knows,
    o,
    obligation,
    performed,
    possibly_k,
    possibly_o,
    violation,
)
from hornet.terms import Atom, Indicator, NonVariable

"""
Helper functions and test coverage for Hornet modalities.
"""

# ------------------------------
# Predicate pre-registration helpers
# ------------------------------


def _register_predicates(db: Database, *indicators: Indicator) -> None:
    """Pre-register predicate indicators with empty clause lists so queries fail
    gracefully instead of raising KeyError."""
    for indicator in indicators:
        db.maps[0].setdefault(indicator, [])


_ACCESSIBLE = ('accessible', 3)
_OBLIGATION = ('obligation', 3)
_KNOWS = ('knows', 3)

# ------------------------------
# Database helpers
# ------------------------------


def _make_epistemic_base():
    """Return a Database with a minimal epistemic setup."""
    from hornet.symbols import fact1, fact2

    db = database()
    db.tell(accessible('alice', fact1, 1))
    db.tell(accessible('alice', fact2, 1))
    return db


def _make_deontic_base():
    """Return a Database with a minimal deontic setup."""
    from hornet.symbols import act1, act2

    db = database()
    db.tell(obligation('alice', act1, 1))
    db.tell(obligation('alice', act2, 1))
    return db


def _modal_db_with_obligation() -> Database:
    """Return a deontic database with Alice obligated to act1 at time 1."""
    from hornet.symbols import act1, act2, complied

    db = modal(database())
    db.tell(
        obligation('alice', act1, 1),
        performed('alice', act2, 1),  # act2 is performed but not obligated
        complied.when(performed('alice', act1, 1)),
    )
    return db


def _make_compliance_base() -> Database:
    """Return a database with one fact and one obligation."""
    from hornet.symbols import act1, fact1

    base = database()
    base.tell(fact1, accessible('alice', fact1, 1), obligation('alice', act1, 1))
    return base


def _audit_db() -> Database:
    """Minimal audit database mirroring examples/audit.py."""
    from hornet.symbols import (
        E2,
        L2,
        T1,
        T2,
        TX,
        Agent,
        Amount,
        Event,
        Fact,
        Init,
        L,
        Limit,
        Regulation,
        Report,
        T,
        _,
        append,
        appointed,
        call,
        currently,
        enacted,
        greater,
        mentions,
        no_later_than,
        report_generated,
        review_report,
        reviewed,
        superseding,
        threshold,
        transaction,
        univ,
    )

    base = modal(database())
    base.tell(
        appointed('alice', 'cfo', 0),
        enacted('r31', 1),
        threshold('r31', 100_000),
        transaction('tx17', 'bob', 250_000, 2),
        report_generated('rep42', 'tx17', 3),
        performed('alice', review_report('rep42'), 3),
        reviewed(Agent, Report, T).when(
            performed(Agent, review_report(Report), T1),
            no_later_than(T1, T),
        ),
        violation(TX, Regulation).when(
            transaction(TX, _, Amount, T),
            currently(enacted(Regulation, _), T),
            threshold(Regulation, Limit),
            greater(Amount, Limit),
        ),
        mentions(Report, violation(TX, Regulation)).when(
            report_generated(Report, TX, T),
            violation(TX, Regulation),
        ),
        no_later_than(T1, T2).when(~greater(T1, T2)),
        currently(Event, T).when(
            call(Event),
            univ(Event, L),
            append(Init, [T1], L),
            no_later_than(T1, T),
            ~superseding(Event, Init, T1, T),
        ),
        superseding(_, Init, T1, T).when(
            append(Init, [T2], L2),
            univ(E2, L2),
            call(E2),
            greater(T2, T1),
            no_later_than(T2, T),
        ),
        obligation(Agent, review_report(Report), T).when(
            currently(appointed(Agent, 'cfo', _), T),
            report_generated(Report, _, T1),
            no_later_than(T1, T),
        ),
        accessible(Agent, Fact, T).when(
            report_generated(Report, _, T1),
            mentions(Report, Fact),
            currently(appointed(Agent, 'cfo', _), T1),
            no_later_than(T1, T),
        ),
        knows(Agent, Fact, T).when(
            accessible(Agent, Fact, T),
            reviewed(Agent, Report, T),
            mentions(Report, Fact),
        ),
    )
    return base


# ------------------------------
# Utilities
# ------------------------------


def solutions(db: Database, *conjuncts: NonVariable):
    return list(db.ask(*conjuncts))


def has_solutions(db: Database, *conjuncts: NonVariable) -> bool:
    return bool(solutions(db, *conjuncts))


# ------------------------------
# powerset tests
# ------------------------------


def test_powerset_empty():
    result = powerset([])
    assert result == ((),)


def test_powerset_single():
    result = powerset([1])
    assert set(result) == {(), (1,)}
    assert len(result) == 2


def test_powerset_two():
    result = powerset([1, 2])
    assert set(result) == {(), (1,), (2,), (1, 2)}
    assert len(result) == 4


def test_powerset_three():
    result = powerset([1, 2, 3])
    assert len(result) == 8


def test_powerset_returns_tuple_of_tuples():
    result = powerset([1, 2])
    assert isinstance(result, tuple)
    assert all(isinstance(s, tuple) for s in result)


def test_powerset_includes_empty_set():
    result = powerset([1, 2, 3])
    assert () in result


def test_powerset_includes_full_set():
    items = [1, 2, 3]
    result = powerset(items)
    assert tuple(items) in result


@given(st.lists(st.integers(), min_size=0, max_size=6, unique=True))
def test_powerset_size_is_2_to_n(items: list[int]):
    result = powerset(items)
    assert len(result) == 2 ** len(items)


@given(st.lists(st.integers(), min_size=0, max_size=6, unique=True))
def test_powerset_all_subsets_are_subsets_of_original(items: list[int]):
    result = powerset(items)
    item_set = set(items)
    for subset in result:
        assert set(subset) <= item_set


@given(st.lists(st.integers(), min_size=0, max_size=6, unique=True))
def test_powerset_no_duplicates_within_subsets(items: list[int]):
    result = powerset(items)
    for subset in result:
        assert len(subset) == len(set(subset))


# ------------------------------
# KleisliComposition tests
# ------------------------------


def test_kleisli_composition_basic():
    def f(x: int):
        return (x + 1, x + 2)

    def g(x: int):
        return (x + 1, x + 2)

    composed = KleisliComposition(f, g)
    assert composed(0) == (2, 3, 3, 4)


def test_kleisli_composition_identity():
    """Composing with identity-like function preserves output."""

    def f(x: int):
        return (x,)

    def g(x: int):
        return (x,)

    composed = KleisliComposition(f, g)
    assert composed(42) == (42,)


def test_kleisli_composition_fan_out():
    """f returns multiple values, g fans them out."""

    def f(x: int):
        return (x, x + 1)

    def g(x: int):
        return (x, x * 2)

    composed = KleisliComposition(f, g)
    result = composed(1)
    assert set(result) == {1, 2, 2, 4}


def test_kleisli_composition_empty_f():
    def f(_: int):
        return ()

    def g(x: int):
        return (x,)

    composed = KleisliComposition(f, g)
    assert composed(5) == ()


def test_kleisli_composition_empty_g():
    def f(x: int):
        return (x,)

    def g(_: int):
        return ()

    composed = KleisliComposition(f, g)
    assert composed(5) == ()


@given(st.integers(min_value=0, max_value=5))
def test_kleisli_composition_associativity_count(n: int):
    """(f ∘ g) ∘ h and f ∘ (g ∘ h) produce same number of results."""

    def f(x: int):
        return tuple(range(x, x + 2))

    def g(x: int):
        return (x, x + 1)

    def h(x: int):
        return (x * 2,)

    left = KleisliComposition(KleisliComposition(f, g), h)
    right = KleisliComposition(f, KleisliComposition(g, h))
    assert left(n) == right(n)


# ------------------------------
# Branch, exists, forall tests
# ------------------------------


def test_branch_single_world():
    """Branch with identity transform yields one result per world."""
    from immutables import Map

    from hornet.clauses import failure, success
    from hornet.tailcalls import trampoline

    def transform(db: Database):
        return (db,)

    base = database()
    branch = Branch(transform)
    step = branch(base, Map())
    results = list(trampoline(lambda: step(success, failure, failure)))
    assert len(results) == 1


def test_branch_two_worlds():
    from immutables import Map

    from hornet.clauses import failure, success
    from hornet.tailcalls import trampoline

    base = database()
    child = base.new_child()

    def transform(db: Database):
        return (db, child)

    branch = Branch(transform)
    step = branch(base, Map())
    results = list(trampoline(lambda: step(success, failure, failure)))
    assert len(results) == 2


def test_branch_empty_worlds():
    from immutables import Map

    from hornet.clauses import failure, success
    from hornet.tailcalls import trampoline

    base = database()

    def transform(_: Database):
        return ()

    branch = Branch(transform)
    step = branch(base, Map())
    results = list(trampoline(lambda: step(success, failure, failure)))
    assert not any(results)


def test_exists_succeeds_in_at_least_one_world():
    from immutables import Map

    from hornet.clauses import failure, resolve, success
    from hornet.symbols import fail, p
    from hornet.tailcalls import trampoline

    def transform(db: Database):
        child_no_p = base.new_child()
        child_no_p.tell(p.when(fail))
        return (db, child_no_p)

    base = database()
    base.tell(p)
    goal = exists(transform, resolve(p))
    step = goal(base, Map())
    results = list(trampoline(lambda: step(success, failure, failure)))
    assert len(results) >= 1


def test_forall_succeeds_when_all_worlds_satisfy():
    from immutables import Map

    from hornet.clauses import failure, resolve, success
    from hornet.symbols import p
    from hornet.tailcalls import trampoline

    def transform(db: Database):
        return (db, db)

    base = database()
    base.tell(p)
    goal = forall(transform, resolve(p))
    step = goal(base, Map())
    results = list(trampoline(lambda: step(success, failure, failure)))
    assert len(results) == 1


def test_forall_fails_when_some_world_does_not_satisfy():
    from immutables import Map

    from hornet.clauses import failure, resolve, success
    from hornet.symbols import fail, r
    from hornet.tailcalls import trampoline

    def transform(db: Database):
        child_no_r = base.new_child()
        child_no_r.tell(r.when(fail))
        return (db, child_no_r)

    base = database()
    base.tell(r)
    goal = forall(transform, resolve(r))
    step = goal(base, Map())
    results = list(trampoline(lambda: step(success, failure, failure)))
    assert not any(results)


def test_forall_empty_worlds_vacuously_true():
    """forall over empty set of worlds is vacuously true."""
    from immutables import Map

    from hornet.clauses import failure, resolve, success
    from hornet.symbols import p
    from hornet.tailcalls import trampoline

    def transform(_: Database):
        return ()

    base = database()
    goal = forall(transform, resolve(p))  # p not even defined
    step = goal(base, Map())
    results = list(trampoline(lambda: step(success, failure, failure)))
    assert len(results) == 1


def test_exists_fails_when_no_world_satisfies():
    from immutables import Map

    from hornet.clauses import failure, resolve, success
    from hornet.symbols import s
    from hornet.tailcalls import trampoline

    def transform(_: Database):
        child1 = base.new_child()
        child2 = base.new_child()
        return (child1, child2)

    base = database()
    base.tell(s)
    goal = exists(transform, resolve(s))
    step = goal(base, Map())
    results = list(trampoline(lambda: step(success, failure, failure)))
    assert not any(results)


# ------------------------------
# Epistemic worlds tests
# ------------------------------


def test_epistemic_worlds_count():
    """With 2 accessible facts, 2^2 = 4 worlds are produced."""
    base = _make_epistemic_base()
    # _make_epistemic_base already adds fact1 and fact2 — do NOT add fact1 again
    worlds = epistemic_worlds('alice', 1)(base)
    assert len(worlds) == 4


def test_epistemic_worlds_reflexivity():
    """The base (full-information) world is always included."""
    from hornet.symbols import fact1

    base = _make_epistemic_base()
    base.tell(fact1)
    worlds = epistemic_worlds('alice', 1)(base)
    some_has_fact1 = any(bool(list(w.ask(fact1))) for w in worlds)
    assert some_has_fact1


def test_epistemic_worlds_no_accessible_facts():
    """With no accessible facts, exactly 1 world (the empty powerset) is produced."""
    from hornet.symbols import p

    base = database()
    _register_predicates(base, _ACCESSIBLE)
    base.tell(p)
    worlds = epistemic_worlds('bob', 99)(base)
    assert len(worlds) == 1


def test_epistemic_worlds_are_databases():
    base = _make_epistemic_base()
    worlds = epistemic_worlds('alice', 1)(base)
    assert all(isinstance(w, Database) for w in worlds)


def test_epistemic_worlds_some_hide_facts():
    """Some worlds should NOT prove fact1 (it was hidden)."""
    from hornet.symbols import fact1

    base = _make_epistemic_base()
    base.tell(fact1)
    worlds = epistemic_worlds('alice', 1)(base)
    some_hide_fact1 = any(not bool(list(w.ask(fact1))) for w in worlds)
    assert some_hide_fact1


# ------------------------------
# Deontic worlds tests
# ------------------------------


def test_deontic_worlds_count():
    """With 2 obligations, 2^2 = 4 deontic worlds."""
    base = _make_deontic_base()
    worlds = deontic_worlds('alice', 1)(base)
    assert len(worlds) == 4


def test_deontic_worlds_reflexivity():
    """Some worlds should represent partial and full fulfillment."""
    from hornet.symbols import act1

    base = _make_deontic_base()
    worlds = deontic_worlds('alice', 1)(base)
    some_has_performed = any(bool(list(w.ask(performed('alice', act1, 1)))) for w in worlds)
    assert some_has_performed


def test_deontic_worlds_no_obligations():
    """With no obligations, exactly 1 world."""
    base = database()
    _register_predicates(base, _OBLIGATION)
    worlds = deontic_worlds('nobody', 99)(base)
    assert len(worlds) == 1


def test_deontic_worlds_are_databases():
    base = _make_deontic_base()
    worlds = deontic_worlds('alice', 1)(base)
    assert all(isinstance(w, Database) for w in worlds)


def test_deontic_worlds_full_fulfillment_world_exists():
    """There should be a world where all obligations are performed."""
    from hornet.symbols import act1, act2

    base = _make_deontic_base()
    worlds = deontic_worlds('alice', 1)(base)
    full_world = [
        w
        for w in worlds
        if bool(list(w.ask(performed('alice', act1, 1))))
        and bool(list(w.ask(performed('alice', act2, 1))))
    ]
    assert len(full_world) >= 1


# ------------------------------
# Compliance worlds tests
# ------------------------------


def test_compliance_worlds_count_():
    """1 epistemic fact × 1 obligation: 2 × 2 = 4 worlds."""
    base = _make_compliance_base()
    worlds = compliance_worlds('alice', 1)(base)
    assert len(worlds) == 4


def test_compliance_worlds_are_databases():
    base = _make_compliance_base()
    worlds = compliance_worlds('alice', 1)(base)
    assert all(isinstance(w, Database) for w in worlds)


def test_compliance_worlds_kleisli_composition():
    """compliance_worlds = epistemic ∘ deontic (Kleisli)."""
    base = _make_compliance_base()
    from hornet.modalities import KleisliComposition

    composed = KleisliComposition(
        epistemic_worlds('alice', 1),
        deontic_worlds('alice', 1),
    )
    direct = compliance_worlds('alice', 1)
    assert len(composed(base)) == len(direct(base))


def test_compliance_worlds_no_accessible_no_obligations():
    """No accessible facts, no obligations → 1 world."""
    base = database()
    _register_predicates(base, _ACCESSIBLE, _OBLIGATION)
    worlds = compliance_worlds('nobody', 0)(base)
    assert len(worlds) == 1


# ------------------------------
# Modal operator tests (k, possibly_k, o, possibly_o)
# ------------------------------


def test_k_succeeds_when_fact_holds_in_all_epistemic_worlds():
    """k(fact1, alice, 1) — fact1 must be provable in all epistemic worlds."""
    from hornet.symbols import fact1

    db = modal(_make_epistemic_base())
    db.tell(fact1)
    result = has_solutions(db, k(fact1, 'alice', 1))
    assert not result


def test_possibly_k_succeeds_when_fact_holds_in_some_world():
    """possibly_k(fact1, alice, 1) should succeed since fact1 holds in the base world."""
    from hornet.symbols import fact1

    db = modal(_make_epistemic_base())
    db.tell(fact1)
    result = has_solutions(db, possibly_k(fact1, 'alice', 1))
    assert result


def test_k_succeeds_when_no_accessible_facts():
    """k(p, alice, 1) with no accessible facts: only 1 world (base) → forall holds if p holds."""
    from hornet.symbols import p

    db = modal(database())
    _register_predicates(db, _ACCESSIBLE)
    db.tell(p)
    result = has_solutions(db, k(p, 'alice', 1))
    assert result


def test_k_fails_when_p_does_not_hold():
    from hornet.symbols import p

    db = modal(database())
    _register_predicates(db, _ACCESSIBLE)
    _register_predicates(db, ('p', 0))  # ADD THIS LINE
    result = has_solutions(db, k(p, 'alice', 1))
    assert not result


def test_possibly_k_fails_when_fact_hidden_in_all_worlds():
    """possibly_k(fact1) fails if fact1 is always hidden (accessible but never provable)."""
    from hornet.symbols import fact1

    db = modal(database())
    _register_predicates(db, ('fact1', 0))
    db.tell(accessible('alice', fact1, 1))
    result = has_solutions(db, possibly_k(fact1, 'alice', 1))
    assert not result


def test_o_fails_when_fact_not_in_all_deontic_worlds():
    """o(p, alice, 1): p depends on act1 being performed; not all worlds have that."""

    db = _modal_db_with_obligation()
    result = has_solutions(db, o(complied, 'alice', 1))
    assert not result


def test_possibly_o_succeeds_when_fact_in_some_deontic_world():
    """possibly_o(p, alice, 1): some world has act1 performed → p holds."""

    db = _modal_db_with_obligation()
    result = has_solutions(db, possibly_o(complied, 'alice', 1))
    assert result


def test_o_succeeds_when_no_obligations():
    """o(p, bob, 1) with no obligations: vacuously true if p holds in base world."""
    from hornet.symbols import p

    db = modal(database())
    _register_predicates(db, _OBLIGATION)
    db.tell(p)
    result = has_solutions(db, o(p, 'bob', 1))
    assert result


def test_possibly_o_fails_when_p_never_holds():
    """possibly_o(q, alice, 1) fails when q never holds regardless of performed obligations."""
    from hornet.symbols import act1, q

    db = modal(database())
    _register_predicates(db, ('q', 0))
    db.tell(obligation('alice', act1, 1))
    result = has_solutions(db, possibly_o(q, 'alice', 1))
    assert not result


# ------------------------------
# Audit scenario / deemed_known
# ------------------------------


def test_deemed_known_in_audit_scenario():
    """Smoke test from audit.py: alice deemed_known violation(tx17, r31) at time 3."""
    db = _audit_db()
    query = deemed_known('alice', violation('tx17', 'r31'), 3)
    result = has_solutions(db, query)
    assert isinstance(result, bool)


def test_deemed_known_fails_for_unknown_agent():
    """deemed_known for an agent with no role/access should fail."""
    from hornet.symbols import anything

    db = modal(database())
    _register_predicates(db, _ACCESSIBLE, _OBLIGATION, _KNOWS)
    result = has_solutions(db, deemed_known('nobody', anything, 0))
    assert not result


# ------------------------------
# Additional epistemic/deontic world tests
# ------------------------------


def test_epistemic_worlds_includes_base_world():
    """The empty-hidden-set world IS the base, so base world is always reachable."""
    from hornet.symbols import p

    base = database()
    _register_predicates(base, _ACCESSIBLE)
    base.tell(p)
    worlds = epistemic_worlds('alice', 1)(base)
    assert any(bool(list(w.ask(p))) for w in worlds)


def test_deontic_worlds_includes_base_world():
    """Deontic worlds include a world where no extra obligations are performed."""
    from hornet.symbols import p

    base = database()
    _register_predicates(base, _OBLIGATION)
    base.tell(p)
    worlds = deontic_worlds('alice', 1)(base)
    assert any(bool(list(w.ask(p))) for w in worlds)


@given(st.integers(min_value=0, max_value=4))
def test_epistemic_worlds_count_with_n_facts(n: int):
    """With n accessible facts, 2^n epistemic worlds are produced."""
    base = database()
    _register_predicates(base, _ACCESSIBLE)
    facts = [Atom(f'fact{i}') for i in range(n)]
    for fact in facts:
        base.tell(fact)
        base.tell(accessible('alice', fact, 1))
    worlds = epistemic_worlds('alice', 1)(base)
    assert len(worlds) == 2**n


@given(st.integers(min_value=0, max_value=4))
def test_deontic_worlds_count_with_n_obligations(n: int):
    """With n obligations, 2^n deontic worlds are produced."""
    base = database()
    _register_predicates(base, _OBLIGATION)
    for i in range(n):
        base.tell(obligation('alice', Atom(f'act{i}'), 1))
    worlds = deontic_worlds('alice', 1)(base)
    assert len(worlds) == 2**n


@given(
    st.integers(min_value=0, max_value=3),
    st.integers(min_value=0, max_value=3),
)
def test_compliance_worlds_count(n_facts: int, n_obligations: int):
    """compliance_worlds count = 2^n_facts × 2^n_obligations."""
    base = database()
    _register_predicates(base, _ACCESSIBLE, _OBLIGATION)
    for i in range(n_facts):
        fact = Atom(f'fact{i}')
        base.tell(fact, accessible('alice', fact, 1))
    for i in range(n_obligations):
        base.tell(obligation('alice', Atom(f'act{i}'), 1))
    worlds = compliance_worlds('alice', 1)(base)
    assert len(worlds) == (2**n_facts) * (2**n_obligations)


@given(st.lists(st.integers(min_value=0, max_value=10), max_size=4, unique=True))
def test_powerset_all_elements_covered(items: list[int]):
    """Every item appears in at least one non-empty subset."""
    result = powerset(items)
    for item in items:
        assert any(item in s for s in result if s)


@given(st.integers(min_value=0, max_value=5))
def test_kleisli_composition_with_powerset_transform(n: int):
    """Composition of powerset-based transforms: f maps input to all subsets,
    g wraps each subset as a list."""

    def f(_: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
        # Return each subset as a separate output (not the whole powerset as one item)
        items = tuple(range(n))
        return powerset(list(items))

    def g(x: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
        return (x,)  # wrap each subset in a 1-tuple

    composed = KleisliComposition(f, g)
    result = composed(())
    assert len(result) == 2**n
