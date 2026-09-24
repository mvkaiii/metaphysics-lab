"""Version constants for the portable AI distribution contract."""

RELEASE_VERSION = "1.7.1"
PROJECT_CONTRACT_VERSION = "1.2"
RUNTIME_SCHEMA_VERSION = "1.1"
CASE_SCHEMA_VERSION = "1.1"
DISTRIBUTION_RUNTIME_VERSION = "1.2-exp"

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
    "classify_validation_context",
    "build_validation_summary",
    "suggest_inquiries",
    "interpret_structural_evidence",
    "rank_evidence",
    "personalize_ranking",
    "build_interpretation_contract",
    "prepare_historical_calibration",
    "lock_blind_forecast",
    "lock_historical_calibration",
    "finalize_historical_calibration",
    "export_case_markdown",
    "build_delivery_bundle",
    "diagnose_case",
    "plan_case_reconciliation",
    "validate_case",
    "migrate_case",
    "update_case_record",
)
