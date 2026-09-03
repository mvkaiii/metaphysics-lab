from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from engine.distribution.claim_authority_manifest import build_claim_authority_manifest
from engine.distribution.claim_consumption_sampling_eligibility import validate_claim_universe_lock
from engine.distribution.event_family_attribution import EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION
from engine.distribution.prospective_window_scope import resolve_prospective_window_scope
from engine.distribution.structural_policy import MAPPING_PROFILE
from engine.distribution.prospective_claim_authority_set import (
    PROSPECTIVE_CLAIM_AUTHORITY_SET_PROFILE,
    build_claim_authority_set,
    validate_claim_authority_set,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "v1.6-claim-consumption-sampling-eligibility.synthetic.v1.json"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_digest(value: object) -> str:
    rendered = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(rendered).hexdigest()


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _scope(start: str, end: str) -> dict:
    return resolve_prospective_window_scope(
        {"window_start": start, "window_end": end, "timezone": "Asia/Taipei"}
    )


def _per_case_manifest(scope: dict, seed: str) -> dict:
    return build_claim_authority_manifest(
        {
            "scope_policy": scope,
            "structural_candidate_authority": {
                "authority_profile": "synthetic-y1-authority-v1",
                "authority_digest": _sha("structural-" + seed),
            },
            "mapping_profile": MAPPING_PROFILE,
            "phase3_authority": {
                "policy_profile": "synthetic-phase3-authority-v1",
                "policy_digest": _sha("phase3-" + seed),
            },
            "efa_authority": {
                "profile_version": EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION,
                "authority_digest": _sha("efa-" + seed),
            },
            "resolved_target_scope": "yearly",
            "promotion_allowed": False,
        }
    )


def _members() -> tuple[dict, dict, list[dict]]:
    fixture = _fixture()
    protocol = fixture["protocol"]
    source = fixture["source_manifest"]
    source_rows = {row["opaque_case_id"]: row for row in source["records"]}
    a = _per_case_manifest(
        _scope("2026-10-01T00:00:00+08:00", "2026-12-31T23:59:59+08:00"),
        "a",
    )
    b = _per_case_manifest(
        _scope("2027-07-01T00:00:00+08:00", "2027-12-31T23:59:59+08:00"),
        "b",
    )
    members = [
        {
            "opaque_case_id": "case-a",
            "source_record_digest": source_rows["case-a"]["source_record_digest"],
            "claim_authority_manifest": a,
        },
        {
            "opaque_case_id": "case-b",
            "source_record_digest": source_rows["case-b"]["source_record_digest"],
            "claim_authority_manifest": b,
        },
    ]
    return protocol, source, members


def _refresh_claim_lock_digest(lock: dict) -> dict:
    body = {
        "schema_version": lock["schema_version"],
        "sampling_profile": lock["sampling_profile"],
        "sampling_protocol_digest": lock["sampling_protocol_digest"],
        "source_manifest_digest": lock["source_manifest_digest"],
        "claim_authority_profile": lock["claim_authority_profile"],
        "claim_authority_digest": lock["claim_authority_digest"],
        "locked_at": lock["locked_at"],
        "cases": sorted(lock["cases"], key=lambda row: row["opaque_case_id"]),
    }
    lock["claim_universe_digest"] = _canonical_digest(body)
    return lock


def _claim_lock(protocol: dict, source: dict, composite: dict) -> dict:
    fixture = _fixture()
    lock = copy.deepcopy(fixture["claim_universe_lock"])
    lock["sampling_protocol_digest"] = protocol["protocol_digest"]
    lock["source_manifest_digest"] = source["source_manifest_digest"]
    lock["claim_authority_profile"] = composite["claim_authority_profile"]
    lock["claim_authority_digest"] = composite["claim_authority_digest"]
    return _refresh_claim_lock_digest(lock)


class ProspectiveClaimAuthoritySetTests(unittest.TestCase):
    def test_two_include_cases_build_one_valid_set(self) -> None:
        protocol, source, members = _members()
        result = build_claim_authority_set(protocol, source, members, promotion_allowed=False)
        self.assertEqual(result["claim_authority_profile"], PROSPECTIVE_CLAIM_AUTHORITY_SET_PROFILE)
        self.assertEqual([row["opaque_case_id"] for row in result["case_authorities"]], ["case-a", "case-b"])
        self.assertNotEqual(
            result["case_authorities"][0]["claim_authority_digest"],
            result["case_authorities"][1]["claim_authority_digest"],
        )
        self.assertEqual(validate_claim_authority_set(result, protocol, source), result)

    def test_reversed_input_order_is_identical(self) -> None:
        protocol, source, members = _members()
        left = build_claim_authority_set(protocol, source, members, promotion_allowed=False)
        right = build_claim_authority_set(protocol, source, list(reversed(members)), promotion_allowed=False)
        self.assertEqual(left, right)

    def test_duplicate_case_id_fails_closed(self) -> None:
        protocol, source, members = _members()
        duplicated = [members[0], copy.deepcopy(members[0]), members[1]]
        with self.assertRaises(ValueError):
            build_claim_authority_set(protocol, source, duplicated, promotion_allowed=False)

    def test_missing_include_case_fails_closed(self) -> None:
        protocol, source, members = _members()
        with self.assertRaises(ValueError):
            build_claim_authority_set(protocol, source, members[:1], promotion_allowed=False)

    def test_excluded_case_fails_closed(self) -> None:
        protocol, source, members = _members()
        source_rows = {row["opaque_case_id"]: row for row in source["records"]}
        extra = copy.deepcopy(members[0])
        extra["opaque_case_id"] = "case-c"
        extra["source_record_digest"] = source_rows["case-c"]["source_record_digest"]
        with self.assertRaises(ValueError):
            build_claim_authority_set(protocol, source, members + [extra], promotion_allowed=False)

    def test_foreign_case_fails_closed(self) -> None:
        protocol, source, members = _members()
        extra = copy.deepcopy(members[0])
        extra["opaque_case_id"] = "case-foreign"
        extra["source_record_digest"] = _sha("foreign-source")
        with self.assertRaises(ValueError):
            build_claim_authority_set(protocol, source, members + [extra], promotion_allowed=False)

    def test_tampered_per_case_manifest_fails_closed(self) -> None:
        protocol, source, members = _members()
        tampered = copy.deepcopy(members)
        tampered[0]["claim_authority_manifest"]["claim_authority_digest"] = "0" * 64
        with self.assertRaises(ValueError):
            build_claim_authority_set(protocol, source, tampered, promotion_allowed=False)

    def test_changing_window_policy_changes_composite_digest(self) -> None:
        protocol, source, members = _members()
        left = build_claim_authority_set(protocol, source, members, promotion_allowed=False)
        changed = copy.deepcopy(members)
        changed[0]["claim_authority_manifest"] = _per_case_manifest(
            _scope("2026-07-01T00:00:00+08:00", "2026-12-31T23:59:59+08:00"),
            "a",
        )
        right = build_claim_authority_set(protocol, source, changed, promotion_allowed=False)
        self.assertNotEqual(left["claim_authority_digest"], right["claim_authority_digest"])

    def test_changing_semantic_authority_changes_composite_digest(self) -> None:
        protocol, source, members = _members()
        left = build_claim_authority_set(protocol, source, members, promotion_allowed=False)
        changed = copy.deepcopy(members)
        scope = _scope("2026-10-01T00:00:00+08:00", "2026-12-31T23:59:59+08:00")
        changed[0]["claim_authority_manifest"] = _per_case_manifest(scope, "changed-authority")
        right = build_claim_authority_set(protocol, source, changed, promotion_allowed=False)
        self.assertNotEqual(left["claim_authority_digest"], right["claim_authority_digest"])

    def test_unknown_input_member_and_output_fields_fail_closed(self) -> None:
        protocol, source, members = _members()
        bad_member = copy.deepcopy(members)
        bad_member[0]["unknown"] = True
        with self.assertRaises(ValueError):
            build_claim_authority_set(protocol, source, bad_member, promotion_allowed=False)

        result = build_claim_authority_set(protocol, source, members, promotion_allowed=False)
        result["unknown"] = True
        with self.assertRaises(ValueError):
            validate_claim_authority_set(result, protocol, source)

    def test_promotion_true_fails_closed(self) -> None:
        protocol, source, members = _members()
        with self.assertRaises(ValueError):
            build_claim_authority_set(protocol, source, members, promotion_allowed=True)

    def test_serialized_digest_tamper_fails_closed(self) -> None:
        protocol, source, members = _members()
        result = build_claim_authority_set(protocol, source, members, promotion_allowed=False)
        result["claim_authority_digest"] = "0" * 64
        with self.assertRaises(ValueError):
            validate_claim_authority_set(result, protocol, source)

    def test_source_protocol_linkage_mismatch_fails_closed(self) -> None:
        protocol, source, members = _members()
        bad_protocol = copy.deepcopy(protocol)
        bad_protocol["protocol_digest"] = "0" * 64
        with self.assertRaises(ValueError):
            build_claim_authority_set(bad_protocol, source, members, promotion_allowed=False)

    def test_member_source_record_digest_must_match(self) -> None:
        protocol, source, members = _members()
        bad = copy.deepcopy(members)
        bad[0]["source_record_digest"] = _sha("wrong-source")
        with self.assertRaises(ValueError):
            build_claim_authority_set(protocol, source, bad, promotion_allowed=False)

    def test_frozen_s1_accepts_composite_provenance_unchanged(self) -> None:
        protocol, source, members = _members()
        composite = build_claim_authority_set(protocol, source, members, promotion_allowed=False)
        lock = _claim_lock(protocol, source, composite)
        self.assertEqual(validate_claim_universe_lock(lock, source, protocol), lock)

    def test_s1_missing_include_case_still_fails_with_composite_provenance(self) -> None:
        protocol, source, members = _members()
        composite = build_claim_authority_set(protocol, source, members, promotion_allowed=False)
        lock = _claim_lock(protocol, source, composite)
        lock["cases"] = [row for row in lock["cases"] if row["opaque_case_id"] != "case-b"]
        _refresh_claim_lock_digest(lock)
        with self.assertRaises(ValueError):
            validate_claim_universe_lock(lock, source, protocol)

    def test_s1_empty_claim_set_still_fails_with_composite_provenance(self) -> None:
        protocol, source, members = _members()
        composite = build_claim_authority_set(protocol, source, members, promotion_allowed=False)
        lock = _claim_lock(protocol, source, composite)
        target = next(row for row in lock["cases"] if row["opaque_case_id"] == "case-a")
        target["locked_claim_ids"] = []
        target["claim_case_digest"] = _canonical_digest(
            {"opaque_case_id": target["opaque_case_id"], "locked_claim_ids": []}
        )
        _refresh_claim_lock_digest(lock)
        with self.assertRaises(ValueError):
            validate_claim_universe_lock(lock, source, protocol)

    def test_s1_claim_universe_digest_tamper_still_fails(self) -> None:
        protocol, source, members = _members()
        composite = build_claim_authority_set(protocol, source, members, promotion_allowed=False)
        lock = _claim_lock(protocol, source, composite)
        lock["claim_universe_digest"] = "0" * 64
        with self.assertRaises(ValueError):
            validate_claim_universe_lock(lock, source, protocol)

    def test_arbitrary_provenance_cannot_bypass_s1_case_completeness(self) -> None:
        protocol, source, members = _members()
        composite = build_claim_authority_set(protocol, source, members, promotion_allowed=False)
        lock = _claim_lock(protocol, source, composite)
        lock["claim_authority_profile"] = "synthetic-other-provenance"
        lock["claim_authority_digest"] = _sha("other-provenance")
        lock["cases"] = [row for row in lock["cases"] if row["opaque_case_id"] != "case-b"]
        _refresh_claim_lock_digest(lock)
        with self.assertRaises(ValueError):
            validate_claim_universe_lock(lock, source, protocol)


if __name__ == "__main__":
    unittest.main()
