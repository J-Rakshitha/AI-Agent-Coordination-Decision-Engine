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


def fallback_code_review(
    file_path: str,
    function_name: str | None,
    dev_a: str,
    dev_b: str,
    risk_score: float,
) -> str:
    fn = function_name or "the file"
    tips = []
    if file_path.endswith(".py"):
        tips.append("Use snake_case for functions and add type hints to public APIs.")
    elif file_path.endswith(".js"):
        tips.append("Prefer const/let over var and keep functions under 50 lines.")
    else:
        tips.append("Follow the project's style guide before merging overlapping edits.")

    if risk_score >= 70:
        tips.append(
            f"High overlap risk ({risk_score}%): {dev_a} and {dev_b} should pair-review "
            f"changes in '{fn}' before either pushes."
        )
    else:
        tips.append(f"{dev_a} and {dev_b} should sync on '{fn}' in {file_path} to avoid losing work.")

    tips.append("Add or update unit tests for the modified function.")
    return " ".join(tips)


def fallback_semantic_analysis(
    file_path: str,
    function_name: str | None,
    dev_a: str,
    dev_b: str,
    risk_score: float,
    ast_report: dict,
) -> str:
    fn = function_name or "the file"
    parts = [
        f"{dev_a} and {dev_b} may introduce incompatible logic in '{fn}' ({file_path})."
    ]
    if ast_report.get("signature_changed"):
        parts.append("AST shows signature changes — callers may break after merge.")
    if ast_report.get("complexity_a", 0) > 10 or ast_report.get("complexity_b", 0) > 10:
        parts.append("High cyclomatic complexity increases regression risk.")
    if risk_score >= 60:
        parts.append(f"Semantic risk elevated ({risk_score}%) — require joint review before push.")
    return " ".join(parts)


def fallback_quality_report(metrics: dict) -> str:
    score = metrics.get("quality_score", 50)
    cx = metrics.get("cyclomatic_complexity", 1)
    if score >= 85:
        return f"Quality score {score}/100 — acceptable. Complexity {cx}; maintain test coverage."
    if score >= 65:
        return (
            f"Quality score {score}/100 — moderate. Complexity {cx}; "
            "add docstrings and reduce function length before merge."
        )
    return (
        f"Quality score {score}/100 — needs improvement. Complexity {cx}; "
        "refactor before merging overlapping edits."
    )


def fallback_resolution_strategies(
    dev_a: str,
    dev_b: str,
    file_path: str,
    function_name: str | None,
    sem_risk: float,
    conflict_type: str,
    grade: str,
) -> str:
    fn = function_name or "the target"
    return (
        f"Strategy 1: {dev_a} rebases onto {dev_b}'s branch and resolves {fn} conflicts. "
        f"Strategy 2: split {conflict_type} work — separate PRs for logic vs tests. "
        f"Strategy 3: pair-program given semantic risk {sem_risk}% and grade {grade}."
    )
