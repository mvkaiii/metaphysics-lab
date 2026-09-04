import copy
import unittest

from engine.distribution.claim_consumption_contract import build_claim_consumption_bundle
from engine.distribution.claim_evidence import build_claim_evidence_packets
from engine.distribution.coordination_policy_v2 import build_coordination_bundle
from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.event_family_attribution import EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION
from engine.distribution.hierarchical_claim_authority import HIERARCHICAL_CLAIM_AUTHORITY_PROFILE_VERSION
from engine.distribution.hybrid_claim_composer import HYBRID_CLAIM_COMPOSER_PROFILE_VERSION
from engine.distribution.hybrid_output_contract import HYBRID_OUTPUT_CONTRACT_PROFILE_VERSION
from engine.distribution.interpretation_contract import build_interpretation_contract
from engine.distribution.interpretation_contract_v2 import build_interpretation_contract_v2
from tests.test_distribution_claim_evidence import anchor, feature, structural


def _fixture():
    features = [
        feature(
            'b-role',
            system='bazi',
            domain='career',
            role='target_evidence',
            scope='yearly',
            families=('role_change',),
            dependency='b-role',
        ),
        feature(
            'z-role',
            system='ziwei',
            domain='career',
            role='target_evidence',
            scope='yearly',
            families=('role_change',),
            dependency='z-role',
        ),
    ]
    ranking = rank_evidence(features, target_scope='yearly')
    structural_interpretation = structural(features)
    return features, ranking, structural_interpretation


def _frozen_legacy_outputs(ranking, structural_interpretation):
    v1 = build_interpretation_contract(ranking, anchor())
    claim_bundle = build_claim_evidence_packets(
        base_ranking=ranking,
        structural_interpretation=structural_interpretation,
        domain_interpretation=v1['domain_interpretation'],
    )
    phase3_caps = {
        str(row['primary_domain']): str(row['allowed_specificity'])
        for row in ranking.get('domains', [])
    }
    coordination_bundle = build_coordination_bundle(
        claim_evidence_packets=claim_bundle['packets'],
        target_scope=str(ranking['target_scope']),
        source_ranking_digest=str(ranking['ranking_digest']),
        source_interpretation_digest=str(structural_interpretation['interpretation_digest']),
        phase3_specificity_by_domain=phase3_caps,
    )
    c1_bundle = build_claim_consumption_bundle(
        claim_evidence_bundle=claim_bundle,
        coordination_bundle=coordination_bundle,
    )
    return {
        'claim_evidence_digest': claim_bundle['claim_evidence_digest'],
        'coordination_digest': coordination_bundle['coordination_digest'],
        'claim_consumption_digest': c1_bundle['claim_consumption_digest'],
        'primary_domains': copy.deepcopy(v1['primary_domains']),
        'secondary_domains': copy.deepcopy(v1['secondary_domains']),
    }


class EventFamilyHybridWrapperIntegrationTests(unittest.TestCase):
    def test_v2_exposes_event_family_hybrid_authority_additively(self):
        _, ranking, structural_interpretation = _fixture()
        result = build_interpretation_contract_v2(
            ranking,
            anchor(),
            structural_interpretation=structural_interpretation,
        )

        self.assertEqual(
            result['event_family_attribution_profile_version'],
            EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION,
        )
        self.assertTrue(result['event_family_attribution_digest'])
        self.assertTrue(result['event_family_attribution_children'])

        self.assertEqual(
            result['hierarchical_claim_authority_profile_version'],
            HIERARCHICAL_CLAIM_AUTHORITY_PROFILE_VERSION,
        )
        self.assertTrue(result['hierarchical_claim_authority_digest'])
        self.assertTrue(result['hierarchical_claim_authority_decisions'])

        self.assertEqual(
            result['hybrid_claim_composer_profile_version'],
            HYBRID_CLAIM_COMPOSER_PROFILE_VERSION,
        )
        self.assertTrue(result['hybrid_claim_composer_digest'])
        self.assertTrue(result['hybrid_claim_composer_children'])
        self.assertIsInstance(result['hybrid_composition_groups'], list)

        self.assertEqual(
            result['hybrid_output_contract_profile_version'],
            HYBRID_OUTPUT_CONTRACT_PROFILE_VERSION,
        )
        self.assertTrue(result['hybrid_output_contract_digest'])
        self.assertTrue(result['hybrid_render_units'])
        self.assertTrue(
            all(unit['causality_allowed'] is False for unit in result['hybrid_render_units'])
        )

    def test_v2_hybrid_integration_preserves_frozen_legacy_outputs_and_is_deterministic(self):
        _, ranking, structural_interpretation = _fixture()
        expected = _frozen_legacy_outputs(ranking, structural_interpretation)

        first = build_interpretation_contract_v2(
            ranking,
            anchor(),
            structural_interpretation=structural_interpretation,
        )
        second = build_interpretation_contract_v2(
            ranking,
            anchor(),
            structural_interpretation=structural_interpretation,
        )

        self.assertEqual(first, second)
        self.assertEqual(first['claim_evidence_digest'], expected['claim_evidence_digest'])
        self.assertEqual(first['coordination_digest'], expected['coordination_digest'])
        self.assertEqual(first['claim_consumption_digest'], expected['claim_consumption_digest'])
        self.assertEqual(first['primary_domains'], expected['primary_domains'])
        self.assertEqual(first['secondary_domains'], expected['secondary_domains'])

    def test_v2_hybrid_render_manifest_binds_to_exposed_hcc_and_child_authority(self):
        _, ranking, structural_interpretation = _fixture()
        result = build_interpretation_contract_v2(
            ranking,
            anchor(),
            structural_interpretation=structural_interpretation,
        )

        renderable_ids = {
            row['child_claim_id']
            for row in result['hierarchical_claim_authority_decisions']
            if row['decision'] in {'render', 'render_with_caveat'}
        }
        rendered_ids = {
            child_id
            for unit in result['hybrid_render_units']
            for child_id in unit['member_child_claim_ids']
        }

        self.assertEqual(rendered_ids, renderable_ids)
        self.assertTrue(
            all(
                unit['source_hcc_digest'] == result['hybrid_claim_composer_digest']
                for unit in result['hybrid_render_units']
            )
        )
