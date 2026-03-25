from hornet import database
from hornet.modalities import modal
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
    Tmax,
    _,
    accessible,
    append,
    appointed,
    call,
    currently,
    deemed_known,
    enacted,
    greater,
    knows,
    mentions,
    no_later_than,
    obligation,
    performed,
    report_generated,
    review_report,
    reviewed,
    superseding,
    threshold,
    transaction,
    univ,
    violation,
)


def main() -> None:
    db = modal(database())

    db.tell(
        #
        # Alice was appointed CFO at time 0.
        appointed('alice', 'cfo', 0),
        #
        # Regulation r31 came into force at time 1.
        enacted('r31', 1),
        #
        # Regulation r31 sets a transaction threshold of 100,000.
        threshold('r31', 100_000),
        #
        # Transaction tx17: Bob transferred 250,000 at time 2.
        transaction('tx17', 'bob', 250_000, 2),
        #
        # Report rep42 was generated about transaction tx17 at time 3.
        report_generated('rep42', 'tx17', 3),
        #
        # Alice performed the action of reviewing report rep42 at time 3.
        performed('alice', review_report('rep42'), 3),
        #
        # An agent has reviewed a report by Tmax if they performed the
        # corresponding review action no later than Tmax.
        reviewed(Agent, Report, Tmax).when(
            performed(Agent, review_report(Report), T1),
            no_later_than(T1, Tmax),
        ),
        #
        # A transaction violates a regulation at time T if it exceeds the
        # regulation’s threshold while the regulation is in force.
        violation(TX, Regulation).when(
            transaction(TX, _, Amount, T),
            currently(enacted(Regulation, _), T),
            threshold(Regulation, Limit),
            greater(Amount, Limit),
        ),
        #
        # A report mentions a violation if it concerns a transaction that
        # actually violated a regulation.
        mentions(Report, violation(TX, Regulation)).when(
            report_generated(Report, TX, T),
            violation(TX, Regulation),
        ),
        #
        # Enforce that T1 is no later than T2 (temporal ordering constraint).
        no_later_than(T1, T2).when(~greater(T1, T2)),
        #
        # Event is considered current at time T if it is in the universe of
        # events, appended to the initial sequence, respects the no-later-than
        # constraint, and is not superseded.
        currently(Event, T).when(
            call(Event),
            univ(Event, L),
            append(Init, [T1], L),
            no_later_than(T1, T),
            ~superseding(Event, Init, T1, T),
        ),
        #
        # An event supersedes previous events if it occurs later than them and
        # respects the temporal ordering constraints.
        superseding(_, Init, T1, T).when(
            append(Init, [T2], L2),
            univ(E2, L2),
            call(E2),
            greater(T2, T1),
            no_later_than(T2, T),
        ),
        #
        # An agent is obligated to review a report by Tmax if they held the CFO
        # role at Tmax and the report was generated no later than Tmax.
        obligation(Agent, review_report(Report), Tmax).when(
            currently(appointed(Agent, 'cfo', _), Tmax),
            report_generated(Report, _, T1),
            no_later_than(T1, Tmax),
        ),
        #
        # An agent could have known a fact at Tmax if a report mentioning that
        # fact was generated no later than Tmax.
        accessible(Agent, Fact, Tmax).when(
            report_generated(Report, _, T1),
            mentions(Report, Fact),
            currently(appointed(Agent, 'cfo', _), T1),
            no_later_than(T1, Tmax),
        ),
        #
        # An agent knows a fact at Tmax if they reviewed a report at Tmax that
        # mentions that fact.
        knows(Agent, Fact, Tmax).when(
            accessible(Agent, Fact, Tmax),
            reviewed(Agent, Report, Tmax),
            mentions(Report, Fact),
        ),
    )

    query = deemed_known('alice', violation('tx17', 'r31'), 3)
    print(f'{query}: {any(db.ask(query))}')


if __name__ == '__main__':
    main()
