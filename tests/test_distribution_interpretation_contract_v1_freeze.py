import copy

from engine.distribution.evidence_models import EvidenceFeature
from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.interpretation_contract import build_interpretation_contract


def feature(feature_id='b1', *, system='bazi', domain='career', role='target_evidence', scope='yearly', families=('role_change',), dependency='bazi-yearly'):
    return EvidenceFeature(
        feature_id=feature_id,
        system=system,
        scope=scope,
        reference_window={'label': 'synthetic'},
        primary_domain=domain,
        event_family_support=tuple(families),
        strength_class='strong',
        maturity='stable',
        qualification_status='qualified',
        source_family='synthetic',
        dependency_family=dependency,
        role=role,
        provenance={'fixture': True},
    )


def yearly_ranking():
    return rank_evidence([feature()], target_scope='yearly')


def anchor():
    return {
        'query_anchor_at': '2026-08-31T14:23:00+08:00',
        'query_timezone': 'Asia/Taipei',
        'knowledge_cutoff_at': '2026-08-31T14:23:00+08:00',
        'prospective_window_start': '2026-09-01T00:00:00+08:00',
        'prospective_window_end': '2027-01-31T23:59:59+08:00',
        'question_reference': 'synthetic-v1-freeze',
        'status': 'ok',
    }


def test_v1_contract_does_not_gain_v2_fields():
    result = build_interpretation_contract(yearly_ranking(), anchor())
    assert result['profile_version'] == 'lin_tianji_interpretation_contract_v1-exp'
    assert 'claim_evidence_packets' not in result
    assert 'reading_policy' not in result
    assert 'global_abstentions' not in result


def test_v1_contract_digest_is_deterministic_and_inputs_are_not_mutated():
    ranking = yearly_ranking()
    resolved_anchor = anchor()
    ranking_before = copy.deepcopy(ranking)
    anchor_before = copy.deepcopy(resolved_anchor)
    first = build_interpretation_contract(ranking, resolved_anchor)
    second = build_interpretation_contract(ranking, resolved_anchor)
    assert first == second
    assert first['interpretation_contract_digest'] == second['interpretation_contract_digest']
    assert ranking == ranking_before
    assert resolved_anchor == anchor_before
