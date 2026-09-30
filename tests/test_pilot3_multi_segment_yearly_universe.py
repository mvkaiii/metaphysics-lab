from __future__ import annotations

import copy
import hashlib
import json
import unittest

from engine.distribution.event_family_attribution import (
    EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION,
)
from tools.pilot3_yearly_claim_universe import (
    MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE,
    MULTI_SEGMENT_YEARLY_UNIVERSE_RULE,
    build_yearly_segment_snapshot_manifest,
    build_multi_segment_yearly_claim_universe,
    validate_locked_claim_ids_against_multi_segment_yearly_universe,
)


def _digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _efa(*child_ids, scope="yearly"):
    body = {
        "profile_version": EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION,
        "target_scope": scope,
        "base_ranking_digest": "1" * 64,
        "structural_interpretation_digest": "2" * 64,
        "children": [{"child_claim_id": child_id} for child_id in child_ids],
    }
    body["event_family_attribution_digest"] = _digest(body)
    return body


def _manifest():
    return build_yearly_segment_snapshot_manifest(
        window_policy_digest="a" * 64,
        snapshots=[
            {
                "snapshot_index": 0,
                "snapshot_id": "segment-a",
                "structural_state_digest": "b" * 64,
            },
            {
                "snapshot_index": 1,
                "snapshot_id": "segment-b",
                "structural_state_digest": "c" * 64,
            },
        ],
    )


class Pilot3MultiSegmentYearlyUniverseTests(unittest.TestCase):
    def test_complete_union_is_the_only_registered_aggregation_rule(self):
        manifest = _manifest()
        result = build_multi_segment_yearly_claim_universe(
            snapshot_manifest=manifest,
            efa_snapshots=[
                {
                    "snapshot_id": "segment-a",
                    "event_family_attribution_bundle": _efa(
                        "child:yearly:career:role_change",
                        "child:yearly:finance:income_change",
                    ),
                },
                {
                    "snapshot_id": "segment-b",
                    "event_family_attribution_bundle": _efa(
                        "child:yearly:career:role_change",
                        "child:yearly:partnership:renegotiation",
                    ),
                },
            ],
        )

        self.assertEqual(
            result["profile_version"],
            MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE,
        )
        self.assertEqual(
            result["aggregation_rule"],
            MULTI_SEGMENT_YEARLY_UNIVERSE_RULE,
        )
        self.assertEqual(
            result["locked_claim_ids"],
            [
                "child:yearly:career:role_change",
                "child:yearly:finance:income_change",
                "child:yearly:partnership:renegotiation",
            ],
        )
        self.assertEqual(result["locked_claim_count"], 3)
        self.assertFalse(result["promotion_allowed"])

    def test_duplicate_child_identity_across_snapshots_is_deduplicated_not_reweighted(self):
        result = build_multi_segment_yearly_claim_universe(
            snapshot_manifest=_manifest(),
            efa_snapshots=[
                {
                    "snapshot_id": "segment-a",
                    "event_family_attribution_bundle": _efa(
                        "child:yearly:career:role_change",
                    ),
                },
                {
                    "snapshot_id": "segment-b",
                    "event_family_attribution_bundle": _efa(
                        "child:yearly:career:role_change",
                    ),
                },
            ],
        )
        self.assertEqual(
            result["locked_claim_ids"],
            ["child:yearly:career:role_change"],
        )
        self.assertEqual(result["locked_claim_count"], 1)

    def test_every_manifest_snapshot_must_have_exactly_one_efa_inventory(self):
        with self.assertRaises(ValueError):
            build_multi_segment_yearly_claim_universe(
                snapshot_manifest=_manifest(),
                efa_snapshots=[
                    {
                        "snapshot_id": "segment-a",
                        "event_family_attribution_bundle": _efa(
                            "child:yearly:career:role_change",
                        ),
                    },
                ],
            )

        with self.assertRaises(ValueError):
            build_multi_segment_yearly_claim_universe(
                snapshot_manifest=_manifest(),
                efa_snapshots=[
                    {
                        "snapshot_id": "segment-a",
                        "event_family_attribution_bundle": _efa(
                            "child:yearly:career:role_change",
                        ),
                    },
                    {
                        "snapshot_id": "segment-b",
                        "event_family_attribution_bundle": _efa(
                            "child:yearly:finance:income_change",
                        ),
                    },
                    {
                        "snapshot_id": "segment-extra",
                        "event_family_attribution_bundle": _efa(
                            "child:yearly:family:care_change",
                        ),
                    },
                ],
            )

    def test_snapshot_order_is_frozen_by_manifest(self):
        manifest = _manifest()
        with self.assertRaises(ValueError):
            build_multi_segment_yearly_claim_universe(
                snapshot_manifest=manifest,
                efa_snapshots=[
                    {
                        "snapshot_id": "segment-b",
                        "event_family_attribution_bundle": _efa(
                            "child:yearly:finance:income_change",
                        ),
                    },
                    {
                        "snapshot_id": "segment-a",
                        "event_family_attribution_bundle": _efa(
                            "child:yearly:career:role_change",
                        ),
                    },
                ],
            )

    def test_pre_efa_manifest_cannot_embed_claim_content(self):
        with self.assertRaises(ValueError):
            build_yearly_segment_snapshot_manifest(
                window_policy_digest="a" * 64,
                snapshots=[
                    {
                        "snapshot_index": 0,
                        "snapshot_id": "segment-a",
                        "structural_state_digest": "b" * 64,
                        "child_count": 999,
                    }
                ],
            )

    def test_non_yearly_or_malformed_efa_fails_closed(self):
        with self.assertRaises(ValueError):
            build_multi_segment_yearly_claim_universe(
                snapshot_manifest=_manifest(),
                efa_snapshots=[
                    {
                        "snapshot_id": "segment-a",
                        "event_family_attribution_bundle": _efa(
                            "child:monthly:career:role_change",
                            scope="monthly",
                        ),
                    },
                    {
                        "snapshot_id": "segment-b",
                        "event_family_attribution_bundle": _efa(
                            "child:yearly:finance:income_change",
                        ),
                    },
                ],
            )

        bad = _efa("child:yearly:career:role_change")
        bad["event_family_attribution_digest"] = "f" * 64
        with self.assertRaises(ValueError):
            build_multi_segment_yearly_claim_universe(
                snapshot_manifest=_manifest(),
                efa_snapshots=[
                    {
                        "snapshot_id": "segment-a",
                        "event_family_attribution_bundle": bad,
                    },
                    {
                        "snapshot_id": "segment-b",
                        "event_family_attribution_bundle": _efa(
                            "child:yearly:finance:income_change",
                        ),
                    },
                ],
            )

    def test_duplicate_child_inside_one_efa_snapshot_fails_closed(self):
        with self.assertRaises(ValueError):
            build_multi_segment_yearly_claim_universe(
                snapshot_manifest=_manifest(),
                efa_snapshots=[
                    {
                        "snapshot_id": "segment-a",
                        "event_family_attribution_bundle": _efa(
                            "child:yearly:career:role_change",
                            "child:yearly:career:role_change",
                        ),
                    },
                    {
                        "snapshot_id": "segment-b",
                        "event_family_attribution_bundle": _efa(
                            "child:yearly:finance:income_change",
                        ),
                    },
                ],
            )

    def test_output_and_digest_are_deterministic(self):
        manifest = _manifest()
        snapshots = [
            {
                "snapshot_id": "segment-a",
                "event_family_attribution_bundle": _efa(
                    "child:yearly:career:role_change",
                    "child:yearly:finance:income_change",
                ),
            },
            {
                "snapshot_id": "segment-b",
                "event_family_attribution_bundle": _efa(
                    "child:yearly:career:role_change",
                    "child:yearly:partnership:renegotiation",
                ),
            },
        ]
        first = build_multi_segment_yearly_claim_universe(
            snapshot_manifest=manifest,
            efa_snapshots=snapshots,
        )
        second = build_multi_segment_yearly_claim_universe(
            snapshot_manifest=copy.deepcopy(manifest),
            efa_snapshots=copy.deepcopy(snapshots),
        )
        self.assertEqual(first, second)
        self.assertEqual(first["claim_universe_digest"], second["claim_universe_digest"])

    def test_s1_lock_must_exactly_match_aggregated_universe(self):
        universe = build_multi_segment_yearly_claim_universe(
            snapshot_manifest=_manifest(),
            efa_snapshots=[
                {
                    "snapshot_id": "segment-a",
                    "event_family_attribution_bundle": _efa(
                        "child:yearly:career:role_change",
                    ),
                },
                {
                    "snapshot_id": "segment-b",
                    "event_family_attribution_bundle": _efa(
                        "child:yearly:finance:income_change",
                    ),
                },
            ],
        )
        self.assertEqual(
            validate_locked_claim_ids_against_multi_segment_yearly_universe(
                [
                    "child:yearly:finance:income_change",
                    "child:yearly:career:role_change",
                ],
                universe,
            )["status"],
            "valid",
        )
        with self.assertRaises(ValueError):
            validate_locked_claim_ids_against_multi_segment_yearly_universe(
                ["child:yearly:career:role_change"],
                universe,
            )


if __name__ == "__main__":
    unittest.main()
