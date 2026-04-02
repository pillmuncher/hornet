from hornet import database
from hornet.clauses import Database, Environment, Subst, predicate, resolve
from hornet.combinators import Step
from hornet.modalities import deontic_worlds, epistemic_worlds, exists, forall, modal
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
    _,
    accessible,
    after,
    appointed,
    deemed_known,
    enacted,
    greater,
    happens_at,
    holds_at,
    in_force,
    initiates,
    mentions,
    obligation,
    published,
    review,
    tenure,
    threshold,
    transaction,
    violated,
    violation,
)


def compliance(db: Database) -> Database:
    """
    Attach the compliance modality to the database.

    This modality encodes the legal notion of "deemed to know" under obligations:
    - For each obligation (deontic world), it considers all possible epistemic
      outcomes accessible to the agent.
    - An agent is considered to "know" a fact if it is accessible in all
      obligation-constrained epistemic worlds.

    In short, it implements the ∀ₒ∃ₖ pattern: for all deontic branches, there
    exists an epistemic branch where the fact is accessible.

    Usage:
        db = compliance(database())
        result = any(db.ask(deemed_known(agent, fact, time)))
    """
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


def main() -> None:
    db = compliance(database())

    # using Robert Kowalski's Event Calculus here:
    db.tell(
        # Regulation reg31 came into force at time 0.
        happens_at(enacted('reg31'), 0),
        # Alice was appointed CFO at time 1.
        happens_at(appointed('alice', 'cfo'), 1),
        # Bob transferred 250,000 at time 2.
        happens_at(transaction('tx17', 'bob', 250_000), 2),
        # Report rep42 was published at time 3.
        happens_at(published('rep42'), 3),
        # Alice did not review report rep42.
        # happens_at(performed('alice', review('rep42'), _))
        # Regulation reg31 sets a transaction threshold of 100,000.
        threshold('reg31', 100_000),
        # Report rep42 mentions transaction tx17.
        mentions('rep42', 'tx17'),
        # Enacting a regulation causes it to be in force.
        initiates(enacted(Regulation), in_force(Regulation)),
        # Appointing an agent to a role causes them to hold that role.
        initiates(appointed(Agent, Role), tenure(Agent, Role)),
        # A transaction violates a regulation if it exceeds the
        # threshold while the regulation is in force.
        violation(TX, Regulation).when(
            happens_at(transaction(TX, _, Amount), T),
            holds_at(in_force(Regulation), T),
            threshold(Regulation, Limit),
            greater(Amount, Limit),
        ),
        # An agent can access a violation if they can access the
        # underlying transaction.
        accessible(Agent, violated(TX, Regulation), Tmax).when(
            accessible(Agent, transaction(TX, Amount), Tmax),
            violation(TX, Regulation),
        ),
        # An agent can access a transaction if a report mentioning it
        # was published while they held the CFO role.
        accessible(Agent, transaction(TX, Amount), Tmax).when(
            mentions(Report, TX),
            happens_at(published(Report), T_report),
            ~after(T_report, Tmax),
            holds_at(tenure(Agent, 'cfo'), Tmax),
        ),
        # An agent is obligated to review a report if it was published
        # while they held the CFO role.
        obligation(Agent, review(Report), T_report).when(
            happens_at(published(Report), T_report),
            holds_at(tenure(Agent, 'cfo'), T_report),
        ),
    )

    # The Query: Is Alice legally "deemed to know" the violation?
    # Logic: In all worlds where she reviews the report (Deontic),
    # she gains access to the transaction data (Epistemic).
    query = deemed_known('alice', violated('tx17', 'reg31'), 3)
    result = any(db.ask(query))
    print(f'Liability Check: {query} -> {result}')


if __name__ == '__main__':
    main()
