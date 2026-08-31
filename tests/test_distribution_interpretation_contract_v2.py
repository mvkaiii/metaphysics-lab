import copy

from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.interpretation_contract import build_interpretation_contract
from engine.distribution.interpretation_contract_v2 import (
    INTERPRETATION_PROFILE_VERSION_V2,
    READING_POLICY,
    build_interpretation_contract_v2,
)
from tests.test_distribution_claim_evidence import anchor, feature, structural


def fixture():
    features = [
        feature('b1', system='bazi', domain='career', role='target_evidence', scope='yearly', dependency='b'),
        feature('z1', system='ziwei', domain='career', role='target_evidence', scope='yearly', dependency='z'),
    ]
    ranking = rank_evidence(features, target_scope='yearly')
    return features, ranking


def test_cold_start_v2_preserves_v1_domain_order_and_adds_vnext_fields():
    features, ranking = fixture()
    v1 = build_interpretation_contract(ranking, anchor())
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
    assert first == second
    assert first['profile_version'] == INTERPRETATION_PROFILE_VERSION_V2
    assert first['primary_domains'] == v1['primary_domains']
    assert first['secondary_domains'] == v1['secondary_domains']
    assert [row['primary_domain'] for row in first['domain_interpretation']] == [row['primary_domain'] for row in v1['domain_interpretation']]
    assert first['claim_evidence_packets']
    assert first['reading_policy'] == READING_POLICY
    assert first['global_abstentions'] == []
    assert first['interpretation_contract_digest']


def test_v2_call_does_not_mutate_or_change_repeated_v1_digest():
    features, ranking = fixture()
    v1_before = build_interpretation_contract(ranking, anchor())
    frozen = copy.deepcopy(v1_before)
    build_interpretation_contract_v2(ranking, anchor(), structural_interpretation=structural(features))
    v1_after = build_interpretation_contract(ranking, anchor())
    assert v1_before == frozen == v1_after
    assert v1_before['interpretation_contract_digest'] == v1_after['interpretation_contract_digest']


def test_no_domain_v2_formally_abstains_domain():
    ranking = rank_evidence([], target_scope='yearly')
    result = build_interpretation_contract_v2(
        ranking,
        anchor(),
        structural_interpretation=structural([], target_scope='yearly'),
    )
    assert result['claim_evidence_packets'] == []
    assert result['global_abstentions'] == ['abstain_domain']


def test_reading_policy_guards_are_guidance_only_and_fail_safe():
    assert READING_POLICY['bazi_order'][0] == 'day_master_and_pillar_roles'
    assert READING_POLICY['ziwei_order'][0] == 'ming_shen_fude'
    guards = READING_POLICY['guards']
    assert all(guards.values())
    assert guards['missing_layer_must_abstain'] is True
    assert guards['five_element_count_is_not_strength_conclusion'] is True
    assert guards['ten_god_is_not_event_formula'] is True
    assert guards['cross_system_conflict_must_be_preserved'] is True
