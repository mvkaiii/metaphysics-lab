import copy

from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.interpretation_contract import build_interpretation_contract
from engine.distribution.interpretation_contract_v2 import build_interpretation_contract_v2
from tests.test_distribution_claim_evidence import anchor, feature, structural


def v2_from(features):
    ranking = rank_evidence(features, target_scope='yearly')
    return ranking, build_interpretation_contract_v2(
        ranking,
        anchor(),
        structural_interpretation=structural(features),
    )


def test_v2_exposes_python_owned_coordination_bundle_for_same_domain_convergence():
    features = [
        feature('b1', system='bazi', domain='career', role='target_evidence', scope='yearly', dependency='b'),
        feature('z1', system='ziwei', domain='career', role='target_evidence', scope='yearly', dependency='z'),
    ]
    _, result = v2_from(features)
    assert result['coordination_policy_version'] == 'lin_tianji_coordination_v1-exp'
    assert result['coordination_digest']
    row = result['coordination_relations'][0]
    assert row['primary_domain'] == 'career'
    assert row['legacy_cross_system_relation'] == 'independent_convergence'
    assert row['coordination_relation'] == 'direct_domain_convergence'
    assert row['same_scope_target_systems'] == ['bazi', 'ziwei']


def test_v2_reclassifies_disjoint_domains_as_parallel_without_rewriting_legacy_packets():
    features = [
        feature('b-car', system='bazi', domain='career', role='target_evidence', scope='yearly', dependency='b-car'),
        feature('z-fin', system='ziwei', domain='finance', role='target_evidence', scope='yearly', dependency='z-fin'),
    ]
    _, result = v2_from(features)
    assert {packet['cross_system_relation'] for packet in result['claim_evidence_packets']} == {'conflict_or_divergence'}
    assert {row['coordination_relation'] for row in result['coordination_relations']} == {'parallel_signals'}
    assert {row['legacy_cross_system_relation'] for row in result['coordination_relations']} == {'conflict_or_divergence'}
    assert result['global_conflicts']


def test_v2_coordination_never_raises_phase3_or_packet_specificity():
    features = [
        feature('b1', system='bazi', domain='career', role='target_evidence', scope='yearly', dependency='b'),
    ]
    ranking, result = v2_from(features)
    packet = result['claim_evidence_packets'][0]
    row = result['coordination_relations'][0]
    phase3 = ranking['domains'][0]['allowed_specificity']
    order = ['domain', 'event_family', 'concrete_event', 'highly_specific_event']
    assert order.index(row['coordination_specificity_cap']) <= order.index(packet['effective_specificity'])
    assert order.index(row['coordination_specificity_cap']) <= order.index(phase3)


def test_v2_coordination_does_not_mutate_v1_and_is_deterministic():
    features = [
        feature('b1', system='bazi', domain='career', role='target_evidence', scope='yearly', dependency='b'),
        feature('z1', system='ziwei', domain='career', role='target_evidence', scope='yearly', dependency='z'),
    ]
    ranking = rank_evidence(features, target_scope='yearly')
    v1_before = build_interpretation_contract(ranking, anchor())
    frozen = copy.deepcopy(v1_before)
    first = build_interpretation_contract_v2(
        ranking,
        anchor(),
        structural_interpretation=structural(features),
    )
    second = build_interpretation_contract_v2(
        ranking,
        anchor(),
        structural_interpretation=structural(features),
    )
    v1_after = build_interpretation_contract(ranking, anchor())
    assert first == second
    assert v1_before == frozen == v1_after
    assert v1_before['interpretation_contract_digest'] == v1_after['interpretation_contract_digest']
    assert first['reading_policy']['guards']['coordination_relation_is_python_authority'] is True
