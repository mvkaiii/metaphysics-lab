import importlib
import importlib.util
import unittest

from engine.distribution.errors import DistributionError
from engine.distribution.event_family_attribution import EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION
from engine.distribution.prospective_window_scope import resolve_prospective_window_scope
from engine.distribution.structural_policy import MAPPING_PROFILE


class DistributionClaimAuthorityManifestTests(unittest.TestCase):
    def _module(self):
        spec = importlib.util.find_spec("engine.distribution.claim_authority_manifest")
        self.assertIsNotNone(
            spec,
            "prospective claim authority requires engine.distribution.claim_authority_manifest",
        )
        return importlib.import_module("engine.distribution.claim_authority_manifest")

    @staticmethod
    def _scope_policy():
        return resolve_prospective_window_scope(
            {
                "window_start": "2026-10-01T00:00:00+08:00",
                "window_end": "2026-12-31T23:59:59+08:00",
                "timezone": "Asia/Taipei",
            }
        )

    def _payload(self, **overrides):
        payload = {
            "scope_policy": self._scope_policy(),
            "structural_candidate_authority": {
                "authority_profile": "lin_tianji_y1_research_candidate_v1",
                "authority_digest": "1" * 64,
            },
            "mapping_profile": MAPPING_PROFILE,
            "phase3_authority": {
                "policy_profile": "lin_tianji_phase3_frozen_v1",
                "policy_digest": "2" * 64,
            },
            "efa_authority": {
                "profile_version": EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION,
                "authority_digest": "3" * 64,
            },
            "resolved_target_scope": "yearly",
            "promotion_allowed": False,
        }
        payload.update(overrides)
        return payload

    def test_valid_manifest_is_deterministic_and_validates(self):
        module = self._module()
        first = module.build_claim_authority_manifest(self._payload())
        second = module.build_claim_authority_manifest(self._payload())

        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "v1.6-prospective-claim-authority-manifest.v1")
        self.assertEqual(
            first["claim_authority_profile"],
            "lin_tianji_prospective_claim_authority_manifest_v1",
        )
        self.assertEqual(first["mapping_profile"], MAPPING_PROFILE)
        self.assertEqual(first["resolved_target_scope"], "yearly")
        self.assertIs(first["promotion_allowed"], False)
        self.assertEqual(module.validate_claim_authority_manifest(first), first)

    def test_manifest_binds_scope_policy_profile_and_digest_only(self):
        module = self._module()
        manifest = module.build_claim_authority_manifest(self._payload())
        scope = manifest["scope_policy"]

        self.assertEqual(
            set(scope),
            {"policy_profile", "policy_digest"},
        )
        self.assertEqual(scope["policy_profile"], self._scope_policy()["policy_profile"])
        self.assertEqual(scope["policy_digest"], self._scope_policy()["policy_digest"])

    def test_resolved_target_scope_must_match_scope_policy_and_v1_yearly_authority(self):
        module = self._module()
        with self.assertRaises(DistributionError) as caught:
            module.build_claim_authority_manifest(
                self._payload(resolved_target_scope="monthly")
            )
        self.assertEqual(caught.exception.code, "invalid_claim_authority_manifest")

    def test_mapping_profile_must_be_the_frozen_structural_mapping_profile(self):
        module = self._module()
        with self.assertRaises(DistributionError) as caught:
            module.build_claim_authority_manifest(
                self._payload(mapping_profile="lin_tianji_domain_future")
            )
        self.assertEqual(caught.exception.code, "invalid_claim_authority_manifest")

    def test_efa_profile_must_bind_the_frozen_efa_profile(self):
        module = self._module()
        payload = self._payload()
        payload["efa_authority"] = {
            "profile_version": "future-efa",
            "authority_digest": "3" * 64,
        }
        with self.assertRaises(DistributionError) as caught:
            module.build_claim_authority_manifest(payload)
        self.assertEqual(caught.exception.code, "invalid_claim_authority_manifest")

    def test_changing_any_semantic_authority_changes_claim_authority_digest(self):
        module = self._module()
        base = module.build_claim_authority_manifest(self._payload())

        variations = []
        structural = self._payload()
        structural["structural_candidate_authority"] = {
            "authority_profile": "lin_tianji_y1_research_candidate_v2",
            "authority_digest": "4" * 64,
        }
        variations.append(structural)

        phase3 = self._payload()
        phase3["phase3_authority"] = {
            "policy_profile": "lin_tianji_phase3_frozen_v1",
            "policy_digest": "5" * 64,
        }
        variations.append(phase3)

        efa = self._payload()
        efa["efa_authority"] = {
            "profile_version": EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION,
            "authority_digest": "6" * 64,
        }
        variations.append(efa)

        for payload in variations:
            with self.subTest(payload=payload):
                changed = module.build_claim_authority_manifest(payload)
                self.assertNotEqual(
                    base["claim_authority_digest"],
                    changed["claim_authority_digest"],
                )

    def test_invalid_sha_shape_fails_closed(self):
        module = self._module()
        payload = self._payload()
        payload["structural_candidate_authority"] = {
            "authority_profile": "lin_tianji_y1_research_candidate_v1",
            "authority_digest": "not-a-sha",
        }
        with self.assertRaises(DistributionError) as caught:
            module.build_claim_authority_manifest(payload)
        self.assertEqual(caught.exception.code, "invalid_claim_authority_manifest")

    def test_promotion_true_fails_closed(self):
        module = self._module()
        with self.assertRaises(DistributionError) as caught:
            module.build_claim_authority_manifest(
                self._payload(promotion_allowed=True)
            )
        self.assertEqual(caught.exception.code, "invalid_claim_authority_manifest")

    def test_unknown_outcome_and_arm_fields_are_rejected(self):
        module = self._module()
        for key, value in (
            ("outcome", "supported"),
            ("oracle", {}),
            ("case_narrative", "private"),
            ("legacy_output", {}),
            ("candidate_output", {}),
            ("q1_result", {}),
            ("t1_result", {}),
        ):
            with self.subTest(key=key):
                with self.assertRaises(DistributionError) as caught:
                    module.build_claim_authority_manifest(
                        self._payload(**{key: value})
                    )
                self.assertEqual(caught.exception.code, "invalid_claim_authority_manifest")

    def test_validator_rejects_digest_tampering(self):
        module = self._module()
        manifest = module.build_claim_authority_manifest(self._payload())
        tampered = dict(manifest)
        tampered["structural_candidate_authority"] = {
            "authority_profile": "lin_tianji_y1_research_candidate_v1",
            "authority_digest": "7" * 64,
        }
        with self.assertRaises(DistributionError) as caught:
            module.validate_claim_authority_manifest(tampered)
        self.assertEqual(caught.exception.code, "invalid_claim_authority_manifest")


if __name__ == "__main__":
    unittest.main()
