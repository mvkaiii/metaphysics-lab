"""Version constants for the portable AI distribution contract."""

PROJECT_CONTRACT_VERSION = "1.1"
RUNTIME_SCHEMA_VERSION = "1.1"
CASE_SCHEMA_VERSION = "1.1"
DISTRIBUTION_RUNTIME_VERSION = "1.1-exp"

SUPPORTED_ACTIONS = (
    "runtime_info",
    "subject.create_identity",
    "subject.registry_validate",
    "subject.rename",
    "subject.prepare_astralium_references",
    "build_natal",
    "natal.candidate_envelope",
    "reconcile_natal",
    "resolve_forecast_context",
    "resolve_query_anchor",
    "lock_prospective_forecast",
    "interpret_structural_evidence",
    "rank_evidence",
    "personalize_ranking",
    "prepare_historical_calibration",
    "lock_blind_forecast",
    "lock_historical_calibration",
    "finalize_historical_calibration",
    "export_case_markdown",
    "build_delivery_bundle",
    "validate_case",
    "migrate_case",
    "update_case_record",
)
