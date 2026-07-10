"""
Rule-based fallback logic.
These functions are passed into HybridAIClient.reason() as `fallback_fn`
so the system keeps working (with slightly less "smart" wording)
even when the LLM API is unreachable.
"""


def fallback_conflict_suggestion(dev_a: str, dev_b: str, file_path: str, function_name: str) -> str:
    return (
        f"{dev_a} and {dev_b} are both editing '{function_name}' in {file_path}. "
        f"Recommended: {dev_a} should pause and sync with {dev_b} before pushing, "
        f"or split the function into smaller units to avoid overlapping changes."
    )


def fallback_root_cause(service_name: str, error_signature: str) -> str:
    known_map = {
        "timeout": "Likely cause: downstream dependency (DB/API) is slow or unresponsive, causing request timeouts.",
        "memory": "Likely cause: memory leak or insufficient memory allocation for the service.",
        "connection_pool": "Likely cause: database connection pool exhaustion, possibly from an unoptimized query or traffic spike.",
        "5xx": "Likely cause: unhandled exception in a recent deployment causing server errors.",
    }
    for key, explanation in known_map.items():
        if key in error_signature.lower():
            return f"[{service_name}] {explanation}"
    return f"[{service_name}] Anomaly detected ({error_signature}). Recommend manual log inspection — no known pattern matched."


def fallback_severity(service_name: str, error_rate: float, affected_users_pct: float) -> str:
    if error_rate > 50 or affected_users_pct > 70:
        return "P1"
    if error_rate > 15 or affected_users_pct > 30:
        return "P2"
    return "P3"


def fallback_remediation_action(root_cause_hint: str) -> str:
    if "connection_pool" in root_cause_hint.lower() or "timeout" in root_cause_hint.lower():
        return "restart_service"
    if "memory" in root_cause_hint.lower():
        return "clear_cache"
    return "notify_oncall_engineer"
