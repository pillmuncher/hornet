from hornet import database
from hornet.modalities import modal
from hornet.symbols import (
    T1,
    TX,
    Action,
    Agent,
    Amount,
    Fact,
    Limit,
    Regulation,
    Report,
    T,
    Tmax,
    _,
    appointed,
    combine,
    compliance_world,
    currently,
    deemed_known,
    enacted,
    epistemic_world,
    greater,
    learned,
    necessarily,
    no_later_than,
    obligation,
    performed,
    report_contains,
    report_generated,
    review_report,
    reviewed,
    threshold,
    transaction,
    uncertain_fact,
    violation,
)


def main() -> None:
    db = modal(database())

    db.tell(
        #
        # Agent is deemed to have known Fact at time Tmax if: in all worlds
        # where Agent fulfilled their obligations (compliance worlds), and in all
        # worlds consistent with what Agent could have known (epistemic worlds),
        # Agent necessarily learned Fact.
        deemed_known(Agent, Fact, Tmax).when(
            necessarily(
                learned(Agent, Fact, Tmax),
                combine(
                    epistemic_world(uncertain_fact(Agent, Fact, Tmax), Agent, Tmax),
                    compliance_world(obligation(Agent, Action, Tmax), Agent, Tmax),
                ),
            )
        ),
        #
        # Agent is obligated to review Report by time Tmax if:
        # - Agent held the CFO role at Tmax,
        # - Report was generated no later than Tmax.
        obligation(Agent, review_report(Report), Tmax).when(
            currently(appointed(Agent, 'cfo', _), Tmax),
            report_generated(Report, _, T1),
            no_later_than(T1, Tmax),
        ),
        #
        # Transaction TX violated Regulation at time T if:
        # - Regulation was in force at time T,
        # - Regulation sets a threshold Limit,
        # - TX transferred Amount at time T,
        # - the transfer Amount met or exceeded Limit.
        violation(TX, Regulation).when(
            transaction(TX, _, Amount, T),
            currently(enacted(Regulation, _), T),
            threshold(Regulation, Limit),
            greater(Amount, Limit),
        ),
        #
        # Fact is epistemically uncertain for Agent at time Tmax if:
        # - Report contains Fact,
        # - Report was generated no later than Tmax,
        # - Agent did not review Report by time Tmax.
        uncertain_fact(Agent, report_contains(Report, Fact), Tmax).when(
            report_generated(Report, _, T1),
            no_later_than(T1, Tmax),
            report_contains(Report, Fact),
            ~reviewed(Agent, Report, Tmax),
        ),
        #
        # Agent learned Fact by time Tmax if they reviewed a Report containing
        # Fact:
        learned(Agent, Fact, Tmax).when(
            reviewed(Agent, Report, Tmax),
            report_contains(Report, Fact),
        ),
        #
        # Agent has reviewed Report by time Tmax if they performed the
        # review_report action no later than Tmax:
        reviewed(Agent, Report, Tmax).when(
            performed(Agent, review_report(Report), T1),
            no_later_than(T1, Tmax),
        ),
        #
        # Report contains a violation if the violation concerns the transaction
        # the report was generated about:
        report_contains(Report, violation(TX, Regulation)).when(
            report_generated(Report, TX, T),
            violation(TX, Regulation),
        ),
        #
        # Alice became CFO at time 0:
        appointed('alice', 'cfo', 0),
        #
        # Regulation r31 came into force at time 1:
        enacted('r31', 1),
        #
        # Regulation r31 sets a transaction limit of $100,000. The threshold
        # carries no independent time index — it is valid for as long as the
        # regulation is in force:
        threshold('r31', 100_000),
        #
        # Bob transferred $250,000 in transaction tx17 at time 2:
        transaction('tx17', 'bob', 250_000, 2),
        #
        # Report rep42 was generated about transaction tx17 at time 3:
        report_generated('rep42', 'tx17', 3),
    )

    # Query
    t_query = 3
    result = any(db.ask(deemed_known('alice', violation('tx17', 'r31'), t_query)))
    print(f"deemed_known('alice', violation('tx17', 'r31'), {t_query}): {result}")


if __name__ == '__main__':
    main()
