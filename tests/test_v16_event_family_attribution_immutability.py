from __future__ import annotations

import hashlib
import json
import unittest

from engine.distribution.claim_evidence import build_claim_evidence_packets
from engine.distribution.evidence_models import EvidenceFeature
from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.event_family_attribution import build_event_family_attribution_bundle


def canonical_digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def feature(feature_id, *, system, family, dependency):
    return EvidenceFeature(
        feature_id=feature_id,
        system=system,
        scope="yearly",
        reference_window={"label": "yearly"},
        primary_domain="career",
        event_family_support=(family,),
        strength_class="strong",
        maturity="stable",
        qualification_status="qualified",
        source_family="synthetic",
        dependency_family=dependency,
        role="target_evidence",
        provenance={"fixture": feature_id},
    )


def structural_bundle(features):
    body = {
        "target_scope": "yearly",
        "features": [item.to_dict() for item in features],
    }
    body["interpretation_digest"] = canonical_digest(body)
    return body


def domain_interpretation_from_ranking(ranking):
    return [
        {
            "primary_domain": row["primary_domain"],
            "event_family_candidates": list(row["event_families"]),
            "effective_specificity": row["allowed_specificity"],
            "base_allowed_specificity": row["allowed_specificity"],
            "evidence_explanation_classes": [],
        }
        for row in ranking["domains"]
    ]


class EventFamilyAttributionImmutabilityTests(unittest.TestCase):
    def setUp(self):
        self.features = [
            feature(
                "bazi-role",
                system="bazi",
                family="role_change",
                dependency="dep:bazi-role",
            ),
            feature(
                "ziwei-leadership",
                system="ziwei",
                family="leadership_change",
                dependency="dep:ziwei-leadership",
            ),
        ]
        self.ranking = rank_evidence(self.features, "yearly")
        self.structural = structural_bundle(self.features)

    def test_efa_does_not_change_phase3_ranking_or_digest(self):
        before = rank_evidence(self.features, "yearly")

        build_event_family_attribution_bundle(
            base_ranking=self.ranking,
            structural_interpretation=self.structural,
        )

        after = rank_evidence(self.features, "yearly")
        self.assertEqual(after, before)
        self.assertEqual(after["ranking_digest"], before["ranking_digest"])

    def test_efa_does_not_change_claim_evidence_output_or_digest(self):
        domain_interpretation = domain_interpretation_from_ranking(self.ranking)
        before = build_claim_evidence_packets(
            base_ranking=self.ranking,
            structural_interpretation=self.structural,
            domain_interpretation=domain_interpretation,
        )

        build_event_family_attribution_bundle(
            base_ranking=self.ranking,
            structural_interpretation=self.structural,
        )

        after = build_claim_evidence_packets(
            base_ranking=self.ranking,
            structural_interpretation=self.structural,
            domain_interpretation=domain_interpretation,
        )
        self.assertEqual(after, before)
        self.assertEqual(after["claim_evidence_digest"], before["claim_evidence_digest"])


if __name__ == "__main__":
    unittest.main()
