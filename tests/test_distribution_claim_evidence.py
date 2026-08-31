import copy
import hashlib
import json

import pytest

from engine.distribution.claim_evidence import build_claim_evidence_packets
from engine.distribution.errors import DistributionError
from engine.distribution.evidence_models import EvidenceFeature
from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.interpretation_contract import build_interpretation_contract
from engine.distribution.structural_policy import MAPPING_PROFILE, STRUCTURAL_PROFILE_VERSION


def canonical_digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def feature(feature_id, *, system='bazi', domain='career', role='target_evidence', scope='yearly', families=('role_change',), dependency=None, maturity='stable', qualification='qualified', strength='strong'):
    return EvidenceFeature(
        feature_id=feature_id,
        system=system,
        scope=scope,
        reference_window={'label': 'synthetic'},
        primary_domain=domain,
        event_family_support=tuple(families),
        strength_class=strength,
        maturity=maturity,
        qualification_status=qualification,
        source_family='synthetic',
        dependency_family=dependency or f'{system}:{scope}:{feature_id}',
        role=role,
        provenance={'fixture': True, 'feature': feature_id},
    )


def anchor():
    return {
        'query_anchor_at': '2026-08-31T14:23:00+08:00',
        'query_timezone': 'Asia/Taipei',
        'knowledge_cutoff_at': '2026-08-31T14:23:00+08:00',
        'prospective_window_start': '2026-09-01T00:00:00+08:00',
        'prospective_window_end': '2027-01-31T23:59:59+08:00',
        'question_reference': 'synthetic-claim-evidence',
        'status': 'ok',
    }


def structural(features, target_scope='yearly'):
    payload = {
        'structural_profile_version': STRUCTURAL_PROFILE_VERSION,
        'mapping_profile_version': MAPPING_PROFILE,
        'target_scope': target_scope,
        'source_context_digest': canonical_digest({'fixture': True}),
        'features': [item.to_dict() for item in features],
    }
    payload['interpretation_digest'] = canonical_digest(payload)
    return payload


def fixture(features=None):
    features = features or [
        feature('b1', system='bazi', domain='career', role='target_evidence', scope='yearly', families=('role_change',), dependency='bazi-target'),
        feature('z1', system='ziwei', domain='career', role='modifier', scope='decadal', families=(), dependency='ziwei-background'),
    ]
    ranking = rank_evidence(features, target_scope='yearly')
    contract = build_interpretation_contract(ranking, anchor())
    return ranking, structural(features), contract['domain_interpretation']


def test_structural_digest_tampering_fails_closed():
    ranking, interpretation, domains = fixture()
    tampered = copy.deepcopy(interpretation)
    tampered['features'][0]['strength_class'] = 'weak'
    with pytest.raises(DistributionError):
        build_claim_evidence_packets(base_ranking=ranking, structural_interpretation=tampered, domain_interpretation=domains)


def test_selected_feature_join_requires_exact_same_domain_resolution():
    ranking, interpretation, domains = fixture()
    missing = copy.deepcopy(interpretation)
    missing['features'] = missing['features'][1:]
    missing['interpretation_digest'] = canonical_digest({k: v for k, v in missing.items() if k != 'interpretation_digest'})
    with pytest.raises(DistributionError):
        build_claim_evidence_packets(base_ranking=ranking, structural_interpretation=missing, domain_interpretation=domains)

    cross = copy.deepcopy(interpretation)
    selected_id = ranking['domains'][0]['feature_ids'][0]
    row = next(item for item in cross['features'] if item['feature_id'] == selected_id)
    row['primary_domain'] = 'finance'
    cross['interpretation_digest'] = canonical_digest({k: v for k, v in cross.items() if k != 'interpretation_digest'})
    with pytest.raises(DistributionError):
        build_claim_evidence_packets(base_ranking=ranking, structural_interpretation=cross, domain_interpretation=domains)


def test_packet_candidate_set_equals_phase3_candidate_set():
    ranking, interpretation, domains = fixture()
    result = build_claim_evidence_packets(base_ranking=ranking, structural_interpretation=interpretation, domain_interpretation=domains)
    assert result['packets'][0]['event_family_candidates'] == ranking['domains'][0]['event_families']


def test_provenance_is_separated_by_system_and_other_systems_rejected():
    ranking, interpretation, domains = fixture()
    result = build_claim_evidence_packets(base_ranking=ranking, structural_interpretation=interpretation, domain_interpretation=domains)
    packet = result['packets'][0]
    assert {row['system'] for row in packet['bazi_evidence']} <= {'bazi'}
    assert {row['system'] for row in packet['ziwei_evidence']} <= {'ziwei'}

    bad_features = [feature('h1', system='historical', domain='career', role='target_evidence')]
    bad_ranking = rank_evidence(bad_features, target_scope='yearly')
    bad_contract = build_interpretation_contract(bad_ranking, anchor())
    with pytest.raises(DistributionError):
        build_claim_evidence_packets(
            base_ranking=bad_ranking,
            structural_interpretation=structural(bad_features),
            domain_interpretation=bad_contract['domain_interpretation'],
        )
