# Copyright (c) 2026 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT
#
# Minimal worked example: should the CFO have known about a violation?
#
# Domain:
#   - transaction tx17 by employee_e for 250,000 at t=1
#   - report rep42 generated about tx17 at t=2
#   - regulation r1 (large transfer) in force from t=0, threshold 100,000
#   - alice holds the cfo role from t=0
#
# Norm:
#   - the cfo is obliged to review all generated reports (rule in force t=0)
#
# Query:
#   treated_as_known(alice, violation(tx17, r1), t=2)?

from hornet.modalities import ClauseStore, base_world, query_treated_as_known
from hornet.symbols import (
    T0,
    T1,
    TX,
    A,
    Agent,
    Amount,
    D,
    Fact,
    Limit,
    R,
    Rpt,
    Rule,
    T,
    after,
    came_into_force,
    greater,
    holds_role,
    learned,
    let,
    obligation,
    performed,
    report_contains,
    report_generated,
    review_report,
    reviewed,
    threshold,
    transaction,
    violation,
)


def main() -> None:
    store = ClauseStore()

    # ── Domain events ────────────────────────────────────────────────
    store.append_domain(transaction('tx17', 'employee_e', 250_000, 1), time=1)
    store.append_domain(report_generated('rep42', 'tx17', 2), time=2)

    # ── Normative acts ───────────────────────────────────────────────
    store.append_normative(came_into_force('r1', 0), time=0)
    store.append_normative(threshold('r1', 0, 100_000), time=0)
    store.append_normative(holds_role('alice', 'cfo', 0), time=0)

    # ── Domain rules ─────────────────────────────────────────────────

    # Violation: a transaction breaches a threshold regulation.
    store.append_rule(
        violation(TX, Rule).when(
            transaction(TX, A, Amount, T),
            threshold(Rule, T0, Limit),
            ~after(T0, T),
            let(D, Amount - Limit),
            greater(D, 0),
        ),
        identity='violation_threshold',
        effective=0,
    )

    # Report content: a report contains the violations associated
    # with the reported transaction.
    store.append_rule(
        report_contains(R, violation(TX, Rule)).when(
            report_generated(R, TX, T),
            violation(TX, Rule),
        ),
        identity='report_contains_violation',
        effective=0,
    )

    # Knowledge from reviewing a report: reviewing a report grounds
    # learned/3 for whatever the report contains.
    store.append_rule(
        learned(Agent, Fact, T).when(
            reviewed(Agent, R, T),
            report_contains(R, Fact),
        ),
        identity='learned_from_review',
        effective=0,
    )

    # Bridge between the deontic and epistemic layers.
    # performed/3 is asserted in compliance worlds by compliance_gen
    # to record that an agent fulfilled their obligations; reviewed/3
    # is the epistemic predicate that grounds learned/3 via report_contains.
    # This rule is what makes constructive knowledge flow from obligation
    # through action to attribution: the CFO is treated as having learned
    # whatever a reviewed report contains, whether or not they actually read it.
    store.append_rule(
        reviewed(Agent, Rpt, T).when(
            performed(Agent, review_report(Rpt), T),
        ),
        identity='reviewed_from_performed',
        effective=0,
    )

    # Obligation rule: cfo must review generated reports.
    store.append_rule(
        obligation(Agent, review_report(Rpt), T).when(
            holds_role(Agent, 'cfo', T0),
            ~after(T0, T),
            report_generated(Rpt, A, T1),
            ~after(T1, T),
        ),
        identity='cfo_review_reports',
        effective=0,
    )

    t_query = 2
    world = base_world(store, t_query)

    # ── Query ────────────────────────────────────────────────────────
    result = query_treated_as_known(world, 'alice', violation('tx17', 'r1'), t_query)
    print(f'treated_as_known(alice, violation(tx17, r1), {t_query}): {result}')


if __name__ == '__main__':
    main()
