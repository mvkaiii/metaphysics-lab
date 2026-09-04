import copy

import pytest

from engine.distribution.coordination_policy_v2 import (
    COORDINATION_POLICY_VERSION,
    build_coordination_bundle,
)


def evidence(system, feature_id, *, scope='yearly', role='target_evidence', dependency=None, maturity='stable'):
    return {
        'feature_id': feature_id,
        'system': system,
        'scope': scope,
        'role': role,
        'strength_class': 'strong',
        'maturity': maturity,
        'qualification_status': 'qualified',
        'source_family': f'synthetic.{system}',
        'dependency_family': dependency or f'dep:{feature_id}',
        'provenance': {'fixture': True},
    }


def packet(domain, *, bazi=(), ziwei=(), legacy=None, specificity='event_family'):
    rows = list(bazi) + list(ziwei)
    return {
        'claim_id': f'claim:yearly:{domain}',
        'primary_domain': domain,
        'event_family_candidates': ['synthetic_family'],
        'time_scope': 'yearly',
        'bazi_evidence': list(bazi),
        'ziwei_evidence': list(ziwei),
        'source_layers': sorted({row['scope'] for row in rows}),
        'independent_support_count': len({row['dependency_family'] for row in rows}),
        'cross_system_relation': legacy,
        'conflicts': [],
        'assumptions': [],
        'base_allowed_specificity': specificity,
        'effective_specificity': specificity,
        'abstention_status': ['abstain_concrete_event'] if specificity != 'concrete_event' else [],
        'confidence_class': 'moderate_confidence',
        'reasoning_chain': {
            'phase3_ranking_digest': 'a' * 64,
            'structural_interpretation_digest': 'b' * 64,
            'selected_feature_ids': [row['feature_id'] for row in rows],
            'specificity_authority': 'phase3_with_existing_local_window_cap',
        },
    }


def build(packets, caps):
    return build_coordination_bundle(
        claim_evidence_packets=packets,
        target_scope='yearly',
        source_ranking_digest='a' * 64,
        source_interpretation_digest='b' * 64,
        phase3_specificity_by_domain=caps,
    )


def test_policy_is_frozen_c_without_runtime_strategy_switch():
    p = packet(
        'career',
        bazi=[evidence('bazi', 'b1')],
        ziwei=[evidence('ziwei', 'z1')],
        legacy='independent_convergence',
        specificity='concrete_event',
    )
    result = build([p], {'career': 'concrete_event'})
    row = result['relations'][0]
    assert result['policy_version'] == COORDINATION_POLICY_VERSION
    assert row['legacy_cross_system_relation'] == 'independent_convergence'
    assert row['coordination_relation'] == 'direct_domain_convergence'
    assert row['same_scope_target_systems'] == ['bazi', 'ziwei']
    assert row['system_support_count'] == 2


def test_disjoint_target_domains_become_parallel_without_rewriting_packets():
    packets = [
        packet('career', bazi=[evidence('bazi', 'b-car')], legacy='conflict_or_divergence'),
        packet('finance', ziwei=[evidence('ziwei', 'z-fin')], legacy='conflict_or_divergence'),
    ]
    before = copy.deepcopy(packets)
    result = build(packets, {'career': 'event_family', 'finance': 'event_family'})
    assert packets == before
    assert {row['coordination_relation'] for row in result['relations']} == {'parallel_signals'}
    for row in result['relations']:
        assert row['legacy_cross_system_relation'] == 'conflict_or_divergence'
        assert row['conflict_evidence_status'] == 'unavailable'
        assert row['parallel_domains'] == ['career', 'finance']


def test_same_system_dependency_fanout_is_separate_from_system_support():
    p = packet(
        'career',
        bazi=[evidence('bazi', 'b1', dependency='dep:1'), evidence('bazi', 'b2', dependency='dep:2')],
        legacy=None,
    )
    row = build([p], {'career': 'event_family'})['relations'][0]
    assert row['dependency_independence_class'] == 'multiple_independent_dependencies'
    assert row['independent_dependency_count'] == 2
    assert row['system_support_count'] == 1
    assert row['coordination_relation'] == 'single_system_support'


def test_layered_complement_is_preserved():
    p = packet(
        'career',
        bazi=[evidence('bazi', 'b1')],
        ziwei=[evidence('ziwei', 'z1', scope='decadal', role='modifier')],
        legacy='layered_complement',
    )
    row = build([p], {'career': 'event_family'})['relations'][0]
    assert row['coordination_relation'] == 'layered_complement'


def test_coordination_specificity_cap_never_exceeds_packet_effective_cap():
    p = packet(
        'career',
        bazi=[evidence('bazi', 'b1')],
        ziwei=[evidence('ziwei', 'z1')],
        legacy='independent_convergence',
        specificity='event_family',
    )
    row = build([p], {'career': 'concrete_event'})['relations'][0]
    assert row['coordination_specificity_cap'] == 'event_family'


def test_missing_required_evidence_field_fails_closed():
    p = packet('career', bazi=[evidence('bazi', 'b1')])
    del p['bazi_evidence'][0]['role']
    with pytest.raises(ValueError):
        build([p], {'career': 'event_family'})


def test_bundle_is_deterministic_for_packet_order():
    packets = [
        packet('career', bazi=[evidence('bazi', 'b-car')], legacy='conflict_or_divergence'),
        packet('finance', ziwei=[evidence('ziwei', 'z-fin')], legacy='conflict_or_divergence'),
    ]
    first = build(packets, {'career': 'event_family', 'finance': 'event_family'})
    second = build(list(reversed(packets)), {'career': 'event_family', 'finance': 'event_family'})
    assert first == second
