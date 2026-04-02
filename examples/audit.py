from hornet import database
from hornet.modalities import modal
from hornet.symbols import (
    TX,
    Agent,
    Amount,
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


def main() -> None:
    db = database()

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
        initiates(enacted(Regulation), enacted(Regulation)),
        # Appointing an agent to a role causes them to hold that role.
        initiates(appointed(Agent, Role), appointed(Agent, Role)),
        # A transaction violates a regulation if it exceeds the
        # threshold while the regulation is in force.
        violation(TX, Regulation).when(
            happens_at(transaction(TX, _, Amount), T),
            holds_at(enacted(Regulation), T),
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
            holds_at(appointed(Agent, 'cfo'), Tmax),
        ),
        # An agent is obligated to review a report if it was published
        # while they held the CFO role.
        obligation(Agent, review(Report), T_report).when(
            happens_at(published(Report), T_report),
            holds_at(appointed(Agent, 'cfo'), T_report),
        ),
    )

    # The Query: Is Alice legally "deemed to know" the violation?
    # Logic: In all worlds where she reviews the report (Deontic),
    # she gains access to the transaction data (Epistemic).
    query = deemed_known('alice', violated('tx17', 'reg31'), 3)
    result = any(modal(db).ask(query))
    print(f'Liability Check: {query} -> {result}')


if __name__ == '__main__':
    main()
