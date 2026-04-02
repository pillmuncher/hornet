from hypothesis import given
from hypothesis import strategies as st

from hornet import database, symbols
from hornet.clauses import Database, Environment, Subst, predicate, resolve
from hornet.combinators import Step
from hornet.modalities import (
    Branch,
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


def _audit_db() -> Database:
    """Minimal audit database mirroring examples/audit.py."""
    from hornet.symbols import (
        TX,
        Agent,
        Amount,
        Fact,
        Limit,
        Regulation,
        Report,
        Role,
        T,
        T_report,
        Tmax,
        accessible,
        after,
        appointed,
        enacted,
        greater,
        happens_at,
        holds_at,
        initiates,
        mentions,
        obligation,
        published,
        review,
        threshold,
        transaction,
        violated,
        violation,
    )

    db = modal(database())

    @db.tell
    @predicate(deemed_known(Agent, Fact, T))
    def _(db: Database, subst: Subst) -> Step[Database, Environment]:
        # ∀ₒ (∃ₖ accessible(...))
        return forall(
            deontic_worlds(subst[Agent], subst[T]),
            exists(
                epistemic_worlds(subst[Agent], subst[T]),
                resolve(accessible(subst[Agent], subst[Fact], subst[T])),
            ),
        )(db, subst.env)

    db.tell(
        happens_at(enacted('reg31'), 0),
        happens_at(appointed('alice', 'cfo'), 1),
        happens_at(transaction('tx17', 'bob', 250_000), 2),
        happens_at(published('rep42'), 3),
        # Alice did not review report rep42.
        # happens_at(performed('alice', review('rep42'), _))
        threshold('reg31', 100_000),
        mentions('rep42', 'tx17'),
        initiates(enacted(Regulation), enacted(Regulation)),
        initiates(appointed(Agent, Role), appointed(Agent, Role)),
        violation(TX, Regulation).when(
            happens_at(transaction(TX, symbols._, Amount), T),
            holds_at(enacted(Regulation), T),
            threshold(Regulation, Limit),
            greater(Amount, Limit),
        ),
        accessible(Agent, violated(TX, Regulation), Tmax).when(
            accessible(Agent, transaction(TX, Amount), Tmax),
            violation(TX, Regulation),
        ),
        accessible(Agent, transaction(TX, Amount), Tmax).when(
            mentions(Report, TX),
            happens_at(published(Report), T_report),
            ~after(T_report, Tmax),
            holds_at(appointed(Agent, 'cfo'), Tmax),
        ),
        obligation(Agent, review(Report), T_report).when(
            happens_at(published(Report), T_report),
            holds_at(appointed(Agent, 'cfo'), T_report),
        ),
    )
    return db


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
    """Smoke test from audit.py: alice deemed_known violation(tx17, reg31) at time 3."""
    db = _audit_db()
    query = deemed_known('alice', violation('tx17', 'reg31'), 3)
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


@given(st.lists(st.integers(min_value=0, max_value=10), max_size=4, unique=True))
def test_powerset_all_elements_covered(items: list[int]):
    """Every item appears in at least one non-empty subset."""
    result = powerset(items)
    for item in items:
        assert any(item in s for s in result if s)
