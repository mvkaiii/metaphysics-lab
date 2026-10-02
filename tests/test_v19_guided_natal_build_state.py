import copy
import unittest

from engine.distribution.runtime import dispatch


PROFILE_ID = "guided-natal-build-v1"
RULE_VERSION = "1.0-exp"

TAIPEI = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "v1.9-test",
    "provider_reference": None,
}

NEW_YORK = {
    "canonical_name": "New York City, USA",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "timezone": "America/New_York",
    "provider_name": "fixture",
    "provider_version": "v1.9-test",
    "provider_reference": "fixture:nyc",
}

IDENTITY = {
    "subject_id": "subj_7f3a2c91d4e8",
    "subject_display_name": "Kai",
    "subject_short_id": "7F3A2C",
    "filename_label": "Kai",
    "status": "active",
}


def exact_birth(time_text="19:20"):
    return {
        "sex": "male",
        "birth_date": "1984-03-13",
        "birth_time_precision": "exact",
        "birth_time": time_text,
        "birth_place": "台北市",
    }


def bounded_birth():
    return {
        "sex": "male",
        "birth_date": "1984-03-13",
        "birth_time_precision": "bounded",
        "birth_time_range": ["19:20", "19:21"],
        "birth_place": "台北市",
    }


class V19GuidedNatalBuildStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.normalized = {}
        for label, time_text in (("old", "19:20"), ("new", "21:20")):
            built = dispatch(
                "build_natal",
                {"birth": exact_birth(time_text), "resolved_location": TAIPEI},
            )
            if not built.get("ok"):
                raise AssertionError(built)
            cls.normalized[label] = built["data"]["normalized_natal"]

        candidate = dispatch(
            "natal.candidate_envelope",
            {"birth": bounded_birth(), "resolved_location": TAIPEI},
        )
        if not candidate.get("ok"):
            raise AssertionError(candidate)
        cls.candidate = candidate["data"]["candidate_envelope"]

    def state(self, **payload):
        return dispatch("natal.guided_build_state", payload)

    def export_case(self, normalized, contract="1.3"):
        result = dispatch(
            "export_case_markdown",
            {
                "normalized_natal": normalized,
                **{key: value for key, value in IDENTITY.items() if key != "status"},
                "generated_at": "2026-10-02T20:00:00+08:00",
                "last_modified_by": "test",
                "project_contract_version": contract,
            },
        )
        self.assertTrue(result["ok"], result)
        return result["data"]

    def test_runtime_advertises_guided_natal_state_authority(self):
        info = dispatch("runtime_info", {})
        self.assertTrue(info["ok"], info)
        self.assertIn("natal.guided_build_state", info["data"]["supported_actions"])
        capability = info["data"]["capabilities"]["distribution.guided_natal_build"]
        self.assertEqual(capability["implementation"], "implemented")
        self.assertEqual(capability["maturity"], "experimental")
        self.assertEqual(capability["routing"], "on_demand")
        self.assertEqual(capability["rule_version"], RULE_VERSION)

    def test_partial_birth_state_requests_only_missing_authoritative_fields(self):
        result = self.state(birth={"birth_date": "1984-03-13"})
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["profile_id"], PROFILE_ID)
        self.assertEqual(data["rule_version"], RULE_VERSION)
        self.assertEqual(data["stage"], "collect_birth_input")
        self.assertEqual(data["next"]["kind"], "user_input")
        self.assertIsNone(data["next"]["action"])
        self.assertEqual(
            set(data["next"]["required_fields"]),
            {"sex", "birth_place", "birth_time_precision"},
        )
        self.assertTrue(data["authority"]["birth_basis_digest"].startswith("gbirth_"))
        self.assertTrue(data["state_digest"].startswith("gstate_"))

    def test_complete_birth_without_location_routes_only_to_location_resolution(self):
        result = self.state(birth=exact_birth())
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["stage"], "resolve_location")
        self.assertEqual(data["next"], {
            "kind": "runtime_action",
            "action": "birth.resolve_location",
            "required_fields": [],
        })

    def test_unique_exact_time_routes_to_exact_natal_builder(self):
        result = self.state(birth=exact_birth(), resolved_location=TAIPEI)
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["stage"], "build_exact_natal")
        self.assertEqual(data["birth_time_precision"], "exact")
        self.assertEqual(data["local_time_resolution"], "unique")
        self.assertEqual(data["next"]["action"], "build_natal")

    def test_exact_dst_fold_routes_to_candidate_envelope_without_auto_selection(self):
        birth = {
            "sex": "male",
            "birth_date": "2026-11-01",
            "birth_time_precision": "exact",
            "birth_time": "01:30",
            "birth_place": "New York City",
        }
        result = self.state(birth=birth, resolved_location=NEW_YORK)
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["stage"], "build_candidate_envelope")
        self.assertEqual(data["birth_time_precision"], "exact")
        self.assertEqual(data["local_time_resolution"], "ambiguous_fold")
        self.assertEqual(data["next"]["action"], "natal.candidate_envelope")

    def test_nonexistent_exact_local_time_blocks_build_instead_of_inventing_time(self):
        birth = {
            "sex": "male",
            "birth_date": "2026-03-08",
            "birth_time_precision": "exact",
            "birth_time": "02:30",
            "birth_place": "New York City",
        }
        result = self.state(birth=birth, resolved_location=NEW_YORK)
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["stage"], "unsupported_local_time")
        self.assertEqual(data["local_time_resolution"], "nonexistent")
        self.assertEqual(data["next"]["kind"], "user_input")
        self.assertIsNone(data["next"]["action"])
        self.assertEqual(data["next"]["required_fields"], ["birth_time"])

    def test_bounded_time_routes_to_candidate_envelope_without_midpoint(self):
        result = self.state(birth=bounded_birth(), resolved_location=TAIPEI)
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["stage"], "build_candidate_envelope")
        self.assertEqual(data["birth_time_precision"], "bounded")
        self.assertIsNone(data["local_time_resolution"])
        self.assertEqual(data["next"]["action"], "natal.candidate_envelope")

    def test_exact_natal_artifact_is_revision_bound_and_ready_for_case_export(self):
        result = self.state(
            birth=exact_birth(),
            resolved_location=TAIPEI,
            normalized_natal=self.normalized["old"],
            subject=IDENTITY,
        )
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["stage"], "ready_case_export")
        self.assertEqual(data["next"]["action"], "export_case_markdown")
        self.assertEqual(data["authority"]["natal_kind"], "normalized_natal")
        self.assertTrue(data["authority"]["natal_revision_id"].startswith("nrev_"))
        self.assertEqual(data["authority"]["subject_id"], IDENTITY["subject_id"])

    def test_candidate_artifact_is_revision_bound_and_ready_for_case_export(self):
        result = self.state(
            birth=bounded_birth(),
            resolved_location=TAIPEI,
            candidate_envelope=self.candidate,
            subject=IDENTITY,
        )
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["stage"], "ready_case_export")
        self.assertEqual(data["authority"]["natal_kind"], "candidate_envelope")
        self.assertTrue(data["authority"]["natal_revision_id"].startswith("nrev_"))

    def test_stale_exact_artifact_cannot_survive_birth_basis_change(self):
        result = self.state(
            birth=exact_birth("21:20"),
            resolved_location=TAIPEI,
            normalized_natal=self.normalized["old"],
            subject=IDENTITY,
        )
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "guided_natal_artifact_basis_mismatch")

    def test_contract_1_3_case_completes_only_when_revision_matches_current_artifact(self):
        exported = self.export_case(self.normalized["old"], "1.3")
        result = self.state(
            birth=exact_birth(),
            resolved_location=TAIPEI,
            normalized_natal=self.normalized["old"],
            subject=IDENTITY,
            case_files=exported["files"],
        )
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["stage"], "complete")
        self.assertEqual(data["next"], {
            "kind": "none",
            "action": None,
            "required_fields": [],
        })
        self.assertEqual(data["authority"]["natal_revision_id"], exported["natal_revision_id"])
        self.assertEqual(data["authority"]["case_natal_revision_id"], exported["natal_revision_id"])
        self.assertEqual(data["authority"]["base_case_digest"], exported["base_case_digest"])
        self.assertEqual(data["authority"]["case_project_contract_version"], "1.3")

    def test_old_case_revision_cannot_be_reused_after_natal_change(self):
        old_case = self.export_case(self.normalized["old"], "1.3")
        result = self.state(
            birth=exact_birth("21:20"),
            resolved_location=TAIPEI,
            normalized_natal=self.normalized["new"],
            subject=IDENTITY,
            case_files=old_case["files"],
        )
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "guided_natal_case_revision_mismatch")

    def test_legacy_case_is_not_declared_complete_and_routes_to_revision_upgrade(self):
        legacy = self.export_case(self.normalized["old"], "1.2")
        result = self.state(
            birth=exact_birth(),
            resolved_location=TAIPEI,
            normalized_natal=self.normalized["old"],
            subject=IDENTITY,
            case_files=legacy["files"],
        )
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["stage"], "case_revision_upgrade_required")
        self.assertEqual(data["authority"]["case_project_contract_version"], "1.2")
        self.assertIsNone(data["authority"]["case_natal_revision_id"])
        self.assertEqual(data["next"]["action"], "case.replace_natal_base")

    def test_snapshot_is_deterministic_and_input_change_changes_state_digest(self):
        payload = {
            "birth": exact_birth(),
            "resolved_location": TAIPEI,
            "normalized_natal": self.normalized["old"],
            "subject": IDENTITY,
        }
        frozen = copy.deepcopy(payload)
        first = self.state(**payload)
        second = self.state(**payload)
        self.assertTrue(first["ok"], first)
        self.assertEqual(first, second)
        self.assertEqual(payload, frozen)

        changed = self.state(
            birth=exact_birth("21:20"),
            resolved_location=TAIPEI,
            normalized_natal=self.normalized["new"],
            subject=IDENTITY,
        )
        self.assertTrue(changed["ok"], changed)
        self.assertNotEqual(first["data"]["state_digest"], changed["data"]["state_digest"])

    def test_case_subject_identity_must_match_current_subject_metadata(self):
        exported = self.export_case(self.normalized["old"], "1.3")
        renamed_subject = dict(IDENTITY)
        renamed_subject["subject_display_name"] = "Kai Renamed"
        renamed_subject["filename_label"] = "Kai-Renamed"

        result = self.state(
            birth=exact_birth(),
            resolved_location=TAIPEI,
            normalized_natal=self.normalized["old"],
            subject=renamed_subject,
            case_files=exported["files"],
        )
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "guided_natal_case_subject_mismatch")

    def test_subject_identity_change_changes_state_digest_before_case_export(self):
        first = self.state(
            birth=exact_birth(),
            resolved_location=TAIPEI,
            normalized_natal=self.normalized["old"],
            subject=IDENTITY,
        )
        renamed_subject = dict(IDENTITY)
        renamed_subject["subject_display_name"] = "Kai Renamed"
        renamed_subject["filename_label"] = "Kai-Renamed"
        renamed = self.state(
            birth=exact_birth(),
            resolved_location=TAIPEI,
            normalized_natal=self.normalized["old"],
            subject=renamed_subject,
        )

        self.assertTrue(first["ok"], first)
        self.assertTrue(renamed["ok"], renamed)
        self.assertEqual(first["data"]["stage"], "ready_case_export")
        self.assertEqual(renamed["data"]["stage"], "ready_case_export")
        self.assertNotEqual(first["data"]["state_digest"], renamed["data"]["state_digest"])

    def test_semantically_equivalent_complete_birth_forms_share_one_state_digest(self):
        explicit = self.state(
            birth=exact_birth(),
            resolved_location=TAIPEI,
        )
        inferred_birth = exact_birth()
        inferred_birth.pop("birth_time_precision")
        inferred = self.state(
            birth=inferred_birth,
            resolved_location=TAIPEI,
        )
        explicit_calendar = exact_birth()
        explicit_calendar["calendar_kind"] = "gregorian"
        with_calendar = self.state(
            birth=explicit_calendar,
            resolved_location=TAIPEI,
        )

        self.assertTrue(explicit["ok"], explicit)
        self.assertEqual(explicit, inferred)
        self.assertEqual(explicit, with_calendar)

    def test_fixed_state_contract_rejects_unknown_top_level_fields(self):
        result = self.state(birth=exact_birth(), invented_memory="do not trust me")
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_guided_natal_state")


if __name__ == "__main__":
    unittest.main()
