import pytest

from engine.distribution.capabilities import get_capability
from engine.distribution.errors import DistributionError
from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.runtime import _build_interpretation_contract_summary
from tests.test_distribution_claim_evidence import anchor, feature, structural


V1 = 'lin_tianji_interpretation_contract_v1-exp'
V2 = 'lin_tianji_interpretation_contract_v2-exp'


def fixture():
    features = [
        feature('b1', system='bazi', domain='career', role='target_evidence', scope='yearly', dependency='b'),
        feature('z1', system='ziwei', domain='career', role='target_evidence', scope='yearly', dependency='z'),
    ]
    return features, rank_evidence(features, target_scope='yearly')


def test_explicit_runtime_v2_profile_returns_v2_contract():
    features, ranking = fixture()
    result = _build_interpretation_contract_summary({
        'base_ranking': ranking,
        'anchor': anchor(),
        'interpretation_profile_version': V2,
        'structural_interpretation': structural(features),
    })
    assert result['profile_version'] == V2
    assert result['claim_evidence_packets']


def test_explicit_v2_requires_structural_interpretation():
    _features, ranking = fixture()
    with pytest.raises(DistributionError) as exc:
        _build_interpretation_contract_summary({
            'base_ranking': ranking,
            'anchor': anchor(),
            'interpretation_profile_version': V2,
        })
    assert exc.value.code == 'invalid_interpretation_contract'


def test_v1_rejects_structural_interpretation_instead_of_ignoring_it():
    features, ranking = fixture()
    with pytest.raises(DistributionError) as exc:
        _build_interpretation_contract_summary({
            'base_ranking': ranking,
            'anchor': anchor(),
            'interpretation_profile_version': V1,
            'structural_interpretation': structural(features),
        })
    assert exc.value.code == 'invalid_interpretation_contract'


def test_unknown_interpretation_profile_fails_closed():
    _features, ranking = fixture()
    with pytest.raises(DistributionError) as exc:
        _build_interpretation_contract_summary({
            'base_ranking': ranking,
            'anchor': anchor(),
            'interpretation_profile_version': 'unknown-profile',
        })
    assert exc.value.code == 'invalid_interpretation_contract'


def test_capability_advertises_v1_and_v2_but_keeps_v1_default_rule_version():
    capability = get_capability('distribution.interpretation_contract')
    assert capability['rule_version'] == V1
    assert capability['routing'] == 'on_demand'
    assert capability['supported_profiles'] == (V1, V2)
