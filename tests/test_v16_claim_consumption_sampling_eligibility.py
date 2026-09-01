from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from engine.distribution.claim_consumption_sampling_eligibility import (
    build_sampling_eligibility_receipt,
    build_sampling_frame,
    validate_claim_universe_lock,
    validate_sampling_frame,
    validate_sampling_protocol,
    validate_sampling_source_manifest,
    verify_oracle_identity_against_sampling_frame,
    verify_sampling_eligibility_receipt,
)
from engine.distribution.claim_consumption_private_threshold import (
    validate_sampling_eligibility_receipt as validate_t1_sampling_receipt,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests' / 'fixtures' / 'v1.6-claim-consumption-sampling-eligibility.synthetic.v1.json'
PUBLIC_PROTOCOL = ROOT / 'qualification' / 'claim_consumption' / 'v1.6' / 'sampling-protocol.complete-census.v1.json'
CLI = ROOT / 'tools' / 'evaluate_v16_claim_consumption_sampling_eligibility.py'
METHOD_DOC = ROOT / 'docs' / 'research' / '2026-09-02-v1.6-claim-consumption-sampling-eligibility-s1.md'


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding='utf-8'))


def refresh_protocol(protocol: dict) -> None:
    protocol.pop('protocol_digest', None)
    protocol['protocol_digest'] = digest(protocol)


def refresh_record(record: dict) -> None:
    facts = {
        'within_cutoff': record['within_cutoff'],
        'candidate_exposure_status': record['candidate_exposure_status'],
        'confirmation_status': record['confirmation_status'],
        'input_validity_status': record['input_validity_status'],
        'scope_status': record['scope_status'],
    }
    record['eligibility_facts_digest'] = digest(facts)
    record['record_digest'] = digest({
        'opaque_case_id': record['opaque_case_id'],
        'source_record_digest': record['source_record_digest'],
        'eligibility_facts_digest': record['eligibility_facts_digest'],
    })


def refresh_source(source: dict) -> None:
    for record in source['records']:
        refresh_record(record)
    source.pop('source_manifest_digest', None)
    normalized = copy.deepcopy(source)
    normalized['records'] = sorted(normalized['records'], key=lambda row: row['opaque_case_id'])
    source['source_manifest_digest'] = digest(normalized)


def refresh_claim_case(row: dict) -> None:
    row['locked_claim_ids'] = sorted(row['locked_claim_ids'])
    row['claim_case_digest'] = digest({'opaque_case_id': row['opaque_case_id'], 'locked_claim_ids': row['locked_claim_ids']})


def refresh_claim_lock(lock: dict) -> None:
    for row in lock['cases']:
        refresh_claim_case(row)
    lock.pop('claim_universe_digest', None)
    normalized = copy.deepcopy(lock)
    normalized['cases'] = sorted(normalized['cases'], key=lambda row: row['opaque_case_id'])
    lock['claim_universe_digest'] = digest(normalized)


def baseline_components() -> tuple[dict, dict, dict]:
    payload = load_fixture()
    return payload['protocol'], payload['source_manifest'], payload['claim_universe_lock']


def build_baseline_frame() -> dict:
    protocol, source, lock = baseline_components()
    return build_sampling_frame(source, lock, protocol, '2026-09-01T15:30:00Z')


class ClaimConsumptionSamplingEligibilityTests(unittest.TestCase):
    def test_protocol_source_and_claim_universe_baseline_validate(self):
        protocol, source, lock = baseline_components()
        self.assertEqual(validate_sampling_protocol(protocol), protocol)
        self.assertEqual(validate_sampling_source_manifest(source, protocol), source)
        self.assertEqual(validate_claim_universe_lock(lock, source, protocol), lock)

    def test_empty_claims_duplicate_claims_and_duplicate_cases_fail_closed(self):
        protocol, source, lock = baseline_components()
        lock['cases'][0]['locked_claim_ids'] = []
        refresh_claim_lock(lock)
        with self.assertRaisesRegex(ValueError, 'claim|empty|non-empty'):
            validate_claim_universe_lock(lock, source, protocol)

        protocol, source, lock = baseline_components()
        lock['cases'][0]['locked_claim_ids'].append(lock['cases'][0]['locked_claim_ids'][0])
        refresh_claim_case(lock['cases'][0])
        lock.pop('claim_universe_digest')
        lock['claim_universe_digest'] = digest({**lock, 'cases': sorted(lock['cases'], key=lambda row: row['opaque_case_id'])})
        with self.assertRaisesRegex(ValueError, 'duplicate|unique'):
            validate_claim_universe_lock(lock, source, protocol)

        protocol, source, lock = baseline_components()
        source['records'].append(copy.deepcopy(source['records'][0]))
        refresh_source(source)
        with self.assertRaisesRegex(ValueError, 'duplicate|unique'):
            validate_sampling_source_manifest(source, protocol)

    def test_protocol_source_and_policy_tamper_fail_closed(self):
        protocol, source, lock = baseline_components()
        protocol['protocol_digest'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'protocol_digest|digest'):
            validate_sampling_protocol(protocol)

        protocol, source, lock = baseline_components()
        source['source_manifest_digest'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'source_manifest_digest|digest'):
            validate_sampling_source_manifest(source, protocol)

        protocol, source, lock = baseline_components()
        source['required_t1_policy_digest'] = 'a' * 64
        refresh_source(source)
        with self.assertRaisesRegex(ValueError, 'policy|T1'):
            validate_sampling_source_manifest(source, protocol)

    def test_exclusion_precedence_is_deterministic(self):
        protocol, source, lock = baseline_components()
        frame = build_sampling_frame(source, lock, protocol, '2026-09-01T15:30:00Z')
        rows = {row['opaque_case_id']: row for row in frame['cases']}
        self.assertEqual(rows['case-d']['status'], 'EXCLUDE_AFTER_CUTOFF')
        self.assertEqual(rows['case-d']['exclusion_reason_code'], 'after_cutoff')

        source['records'] = list(reversed(source['records']))
        frame2 = build_sampling_frame(source, lock, protocol, '2026-09-01T15:30:00Z')
        self.assertEqual(frame['frame_digest'], frame2['frame_digest'])

    def test_claim_universe_case_set_must_equal_derived_include_set(self):
        protocol, source, lock = baseline_components()
        lock['cases'].pop()
        refresh_claim_lock(lock)
        with self.assertRaisesRegex(ValueError, 'case set|INCLUDE|complete'):
            validate_claim_universe_lock(lock, source, protocol)

        protocol, source, lock = baseline_components()
        excluded = {'opaque_case_id': 'case-c', 'locked_claim_ids': ['claim-c1']}
        refresh_claim_case(excluded)
        lock['cases'].append(excluded)
        refresh_claim_lock(lock)
        with self.assertRaisesRegex(ValueError, 'case set|excluded|INCLUDE'):
            validate_claim_universe_lock(lock, source, protocol)

    def test_unknown_fields_fail_closed_at_all_pre_frame_levels(self):
        protocol, source, lock = baseline_components()
        protocol['private_text'] = 'forbidden'
        with self.assertRaisesRegex(ValueError, 'unknown'):
            validate_sampling_protocol(protocol)

        protocol, source, lock = baseline_components()
        source['private_text'] = 'forbidden'
        with self.assertRaisesRegex(ValueError, 'unknown'):
            validate_sampling_source_manifest(source, protocol)

        protocol, source, lock = baseline_components()
        source['records'][0]['private_text'] = 'forbidden'
        refresh_source(source)
        with self.assertRaisesRegex(ValueError, 'unknown'):
            validate_sampling_source_manifest(source, protocol)

        protocol, source, lock = baseline_components()
        lock['private_text'] = 'forbidden'
        refresh_claim_lock(lock)
        with self.assertRaisesRegex(ValueError, 'unknown'):
            validate_claim_universe_lock(lock, source, protocol)

    def test_public_protocol_artifact_validates_and_matches_required_t1_policy(self):
        protocol = json.loads(PUBLIC_PROTOCOL.read_text(encoding='utf-8'))
        self.assertEqual(validate_sampling_protocol(protocol), protocol)
        self.assertEqual(protocol['required_t1_policy_digest'], '65a072b2de63d6f509cc79139442263695589feca28ee99da0ab976ba0c3118a')
        self.assertFalse(protocol['promotion_allowed'])

    def test_valid_complete_census_builds_eligible_t1_compatible_receipt(self):
        protocol, source, lock = baseline_components()
        frame = build_sampling_frame(source, lock, protocol, '2026-09-01T15:30:00Z')
        validate_sampling_frame(frame, source, lock, protocol)
        self.assertEqual(len(frame['cases']), len(source['records']))
        receipt = build_sampling_eligibility_receipt(frame, source, lock, protocol, '2026-09-01T15:31:00Z')
        self.assertEqual(receipt['status'], 'ELIGIBLE')
        self.assertEqual(receipt['case_count'], 2)
        self.assertEqual(receipt['claim_count'], 3)
        self.assertEqual(verify_sampling_eligibility_receipt(receipt), receipt)
        self.assertEqual(validate_t1_sampling_receipt(receipt), receipt)

    def test_zero_new_cases_yields_ineligible_zero_receipt(self):
        protocol, source, lock = baseline_components()
        for record in source['records']:
            record['within_cutoff'] = True
            record['candidate_exposure_status'] = 'PREVIOUSLY_EXPOSED'
            record['confirmation_status'] = 'CONFIRMED'
            record['input_validity_status'] = 'VALID'
            record['scope_status'] = 'IN_SCOPE'
        refresh_source(source)
        lock['source_manifest_digest'] = source['source_manifest_digest']
        lock['cases'] = []
        refresh_claim_lock(lock)
        frame = build_sampling_frame(source, lock, protocol, '2026-09-01T15:30:00Z')
        receipt = build_sampling_eligibility_receipt(frame, source, lock, protocol, '2026-09-01T15:31:00Z')
        self.assertEqual(receipt['status'], 'INELIGIBLE')
        self.assertEqual(receipt['case_count'], 0)
        self.assertEqual(receipt['claim_count'], 0)
        self.assertEqual(validate_t1_sampling_receipt(receipt), receipt)

    def test_frame_mutations_fail_closed(self):
        protocol, source, lock = baseline_components()
        frame = build_sampling_frame(source, lock, protocol, '2026-09-01T15:30:00Z')
        by_id = {row['opaque_case_id']: row for row in frame['cases']}
        by_id['case-c']['status'] = 'INCLUDE'
        by_id['case-c']['exclusion_reason_code'] = None
        by_id['case-c']['locked_claim_ids'] = ['forbidden']
        by_id['case-c']['case_digest'] = digest({
            'opaque_case_id': by_id['case-c']['opaque_case_id'],
            'source_record_digest': by_id['case-c']['source_record_digest'],
            'status': by_id['case-c']['status'],
            'exclusion_reason_code': by_id['case-c']['exclusion_reason_code'],
            'locked_claim_ids': sorted(by_id['case-c']['locked_claim_ids']),
        })
        frame['frame_digest'] = digest({**{k:v for k,v in frame.items() if k != 'frame_digest'}, 'cases': sorted(frame['cases'], key=lambda row: row['opaque_case_id'])})
        with self.assertRaisesRegex(ValueError, 'status|exposed|claim'):
            validate_sampling_frame(frame, source, lock, protocol)

        frame = build_sampling_frame(source, lock, protocol, '2026-09-01T15:30:00Z')
        frame['cases'].pop()
        with self.assertRaisesRegex(ValueError, 'case set|complete|manifest'):
            validate_sampling_frame(frame, source, lock, protocol)

        frame = build_sampling_frame(source, lock, protocol, '2026-09-01T15:30:00Z')
        frame['frame_digest'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'frame_digest|digest'):
            validate_sampling_frame(frame, source, lock, protocol)

        frame = build_sampling_frame(source, lock, protocol, '2026-09-01T15:30:00Z')
        frame['cases'][0]['case_digest'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'case_digest|digest'):
            validate_sampling_frame(frame, source, lock, protocol)

    def test_frame_claim_set_must_equal_claim_universe(self):
        protocol, source, lock = baseline_components()
        frame = build_sampling_frame(source, lock, protocol, '2026-09-01T15:30:00Z')
        include = next(row for row in frame['cases'] if row['status'] == 'INCLUDE')
        include['locked_claim_ids'] = include['locked_claim_ids'][:-1]
        with self.assertRaisesRegex(ValueError, 'claim|universe|case_digest'):
            validate_sampling_frame(frame, source, lock, protocol)

    def test_permutations_do_not_change_frame_or_receipt_digests(self):
        protocol, source, lock = baseline_components()
        frame1 = build_sampling_frame(source, lock, protocol, '2026-09-01T15:30:00Z')
        receipt1 = build_sampling_eligibility_receipt(frame1, source, lock, protocol, '2026-09-01T15:31:00Z')
        source['records'] = list(reversed(source['records']))
        lock['cases'] = list(reversed(lock['cases']))
        for row in lock['cases']:
            row['locked_claim_ids'] = list(reversed(row['locked_claim_ids']))
        frame2 = build_sampling_frame(source, lock, protocol, '2026-09-01T15:30:00Z')
        receipt2 = build_sampling_eligibility_receipt(frame2, source, lock, protocol, '2026-09-01T15:31:00Z')
        self.assertEqual(frame1['frame_digest'], frame2['frame_digest'])
        self.assertEqual(receipt1['receipt_digest'], receipt2['receipt_digest'])

    def test_oracle_identity_exact_set_and_answer_independence(self):
        payload = load_fixture()
        protocol, source, lock = payload['protocol'], payload['source_manifest'], payload['claim_universe_lock']
        frame = build_sampling_frame(source, lock, protocol, '2026-09-01T15:30:00Z')
        first = verify_oracle_identity_against_sampling_frame(frame, payload['oracle'])
        self.assertEqual(first['status'], 'VALID')
        self.assertEqual(first['case_count'], 2)
        self.assertEqual(first['claim_count'], 3)
        self.assertFalse(first['promotion_allowed'])

        changed = copy.deepcopy(payload['oracle'])
        changed['cases'][0]['expectations'][0]['expected_authorization'] = 'render_with_caveat'
        changed['cases'][0]['expectations'][0]['minimum_acceptable_specificity'] = 'domain'
        changed['cases'][0]['expectations'][0]['maximum_specificity'] = 'event_family'
        changed['cases'][0]['expectations'][0]['caveat_required'] = True
        second = verify_oracle_identity_against_sampling_frame(frame, changed)
        self.assertEqual(first, second)

    def test_oracle_missing_extra_claim_or_case_fails(self):
        payload = load_fixture()
        frame = build_baseline_frame()
        oracle = copy.deepcopy(payload['oracle'])
        oracle['cases'][0]['expectations'].pop()
        with self.assertRaisesRegex(ValueError, 'claim|identity'):
            verify_oracle_identity_against_sampling_frame(frame, oracle)

        oracle = copy.deepcopy(payload['oracle'])
        oracle['cases'][0]['expectations'].append(copy.deepcopy(oracle['cases'][0]['expectations'][0]))
        oracle['cases'][0]['expectations'][-1]['claim_id'] = 'extra-claim'
        with self.assertRaisesRegex(ValueError, 'claim|identity'):
            verify_oracle_identity_against_sampling_frame(frame, oracle)

        oracle = copy.deepcopy(payload['oracle'])
        oracle['cases'].pop()
        with self.assertRaisesRegex(ValueError, 'case|identity'):
            verify_oracle_identity_against_sampling_frame(frame, oracle)

        oracle = copy.deepcopy(payload['oracle'])
        extra = copy.deepcopy(oracle['cases'][0])
        extra['case_id'] = 'extra-case'
        oracle['cases'].append(extra)
        with self.assertRaisesRegex(ValueError, 'case|identity'):
            verify_oracle_identity_against_sampling_frame(frame, oracle)

    def test_cli_parity_private_outputs_and_method_governance(self):
        payload = load_fixture()
        protocol, source, lock = payload['protocol'], payload['source_manifest'], payload['claim_universe_lock']
        direct_frame = build_sampling_frame(source, lock, protocol, '2026-09-01T15:30:00Z')
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            pp, sp, lp, op = td/'p.json', td/'s.json', td/'l.json', td/'o.json'
            for path, data in ((pp,protocol),(sp,source),(lp,lock),(op,payload['oracle'])):
                path.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
            frame_out = td/'frame.json'
            proc = subprocess.run([
                sys.executable, str(CLI), 'build-frame', '--protocol', str(pp), '--source-manifest', str(sp),
                '--claim-universe-lock', str(lp), '--locked-at', '2026-09-01T15:30:00Z', '--output', str(frame_out)
            ], cwd=ROOT, capture_output=True, check=True)
            self.assertEqual(proc.stdout, b'')
            self.assertEqual(frame_out.read_bytes(), canonical_bytes(direct_frame)+b'\n')

            receipt_out = td/'receipt.json'
            proc = subprocess.run([
                sys.executable, str(CLI), 'seal-receipt', '--protocol', str(pp), '--source-manifest', str(sp),
                '--claim-universe-lock', str(lp), '--frame', str(frame_out), '--sealed-at', '2026-09-01T15:31:00Z',
                '--output', str(receipt_out)
            ], cwd=ROOT, capture_output=True, check=True)
            direct_receipt = build_sampling_eligibility_receipt(direct_frame, source, lock, protocol, '2026-09-01T15:31:00Z')
            self.assertEqual(receipt_out.read_bytes(), canonical_bytes(direct_receipt)+b'\n')

            ident_out = td/'identity.json'
            subprocess.run([
                sys.executable, str(CLI), 'verify-oracle-identity', '--frame', str(frame_out), '--oracle', str(op), '--output', str(ident_out)
            ], cwd=ROOT, capture_output=True, check=True)
            self.assertEqual(ident_out.read_bytes(), canonical_bytes(verify_oracle_identity_against_sampling_frame(direct_frame,payload['oracle']))+b'\n')

            no_output = subprocess.run([
                sys.executable, str(CLI), 'build-frame', '--protocol', str(pp), '--source-manifest', str(sp),
                '--claim-universe-lock', str(lp), '--locked-at', '2026-09-01T15:30:00Z'
            ], cwd=ROOT, capture_output=True)
            self.assertNotEqual(no_output.returncode, 0)

        text = METHOD_DOC.read_text(encoding='utf-8')
        for marker in ('prospective-only','Complete census','Previously exposed','outcome-free','promotion_allowed=false','does not execute Q1','does not execute T1'):
            self.assertIn(marker, text)

    def test_private_contamination_and_upstream_mutation_guards(self):
        changed = subprocess.run([
            'git','diff','--name-only','2fd80d234a04d40bafe66db21aa96c4a2594e2a1...HEAD'
        ], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
        forbidden_upstream = (
            'engine/distribution/claim_consumption_private_threshold.py',
            'engine/distribution/claim_consumption_oracle_seal.py',
            'engine/distribution/claim_consumption_qualification.py',
            'engine/distribution/claim_consumption_contract.py',
            'engine/distribution/coordination',
        )
        for path in changed:
            self.assertFalse(any(path == x or path.startswith(x) for x in forbidden_upstream), path)

        scan_paths = [
            ROOT/'engine'/'distribution'/'claim_consumption_sampling_eligibility.py',
            ROOT/'tools'/'evaluate_v16_claim_consumption_sampling_eligibility.py',
            ROOT/'tests'/'test_v16_claim_consumption_sampling_eligibility.py',
            METHOD_DOC,
        ]
        forbidden = (
            'q1-'+'private-'+'adjudication',
            'CLAIM_CONSUMPTION_PRIVATE_'+'EQUIVALENCE_EVALUATION',
            'COORDINATION_PRIVATE_'+'EQUIVALENCE_EVALUATION',
        )
        for path in scan_paths:
            text = path.read_text(encoding='utf-8')
            for needle in forbidden:
                self.assertNotIn(needle, text)


if __name__ == '__main__':
    unittest.main()
