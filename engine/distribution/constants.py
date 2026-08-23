"""Version constants for the portable AI distribution contract."""

PROJECT_CONTRACT_VERSION = "1.1"
RUNTIME_SCHEMA_VERSION = "1.0"
CASE_SCHEMA_VERSION = "1.1"
DISTRIBUTION_RUNTIME_VERSION = "1.0-exp"

SUPPORTED_ACTIONS = (
    "runtime_info",
    "subject.create_identity",
    "subject.registry_validate",
    "subject.rename",
    "build_natal",
    "reconcile_natal",
    "resolve_forecast_context",
    "prepare_historical_calibration",
    "lock_blind_forecast",
    "lock_historical_calibration",
    "finalize_historical_calibration",
    "export_case_markdown",
    "validate_case",
    "migrate_case",
    "update_case_record",
)
