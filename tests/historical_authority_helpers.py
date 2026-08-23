"""Test fixtures for Case-backed historical calibration authority."""

from engine.distribution.case_pack import (
    BASE_CASE_FILES,
    CASE_FILES,
    _manifest_expected_line,
    _metadata,
    _render_case_file,
    canonical_case_filename,
)
from engine.distribution.calibration import finalize_historical_calibration, lock_historical_calibration


SUBJECT_ID = "subj_7f3a2c91d4e8"
SHORT_ID = "7F3A2C"
DISPLAY_NAME = "Kai"
WHEN = "2026-08-23T18:00:00+08:00"


def base_case_files():
    identity = {
        "subject_id": SUBJECT_ID,
        "subject_display_name": DISPLAY_NAME,
        "subject_short_id": SHORT_ID,
        "filename_label": DISPLAY_NAME,
    }
    manifest = ["# %s｜Metaphysics Lab Case｜專案索引" % DISPLAY_NAME, "", "## Case Files", ""]
    for canonical in CASE_FILES:
        actual = canonical_case_filename(identity, canonical)
        manifest.append(_manifest_expected_line(canonical, actual, canonical in BASE_CASE_FILES))
    bodies = {"00_專案索引.md": "\n".join(manifest) + "\n"}
    for canonical in BASE_CASE_FILES[1:]:
        bodies[canonical] = "# %s｜%s\n" % (DISPLAY_NAME, canonical[3:-3])
    files = {}
    for canonical in BASE_CASE_FILES:
        actual = canonical_case_filename(identity, canonical)
        files[actual] = _render_case_file(
            canonical,
            _metadata(canonical, identity, WHEN, "test"),
            bodies[canonical],
        )
    return files


def authoritative_lock(payload):
    files = base_case_files()
    request = dict(payload)
    request.update({
        "subject_id": SUBJECT_ID,
        "case_files": files,
        "updated_at": request.get("locked_at", WHEN),
        "last_modified_by": "test",
    })
    locked = lock_historical_calibration(request)
    authoritative = dict(files)
    authoritative.update(locked["changed_files"])
    result = dict(locked)
    result["case_files"] = authoritative
    return result


def authoritative_finalize(locked, payload):
    request = {
        "case_files": locked["case_files"],
        "lock_record_id": locked["lock_record_id"],
        "locked_payload": locked["locked_payload"],
        "payload_digest": locked["payload_digest"],
        "last_modified_by": "test",
    }
    request.update(payload)
    return finalize_historical_calibration(request)
