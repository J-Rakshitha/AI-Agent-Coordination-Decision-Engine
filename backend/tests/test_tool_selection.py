"""
Milestone 2 — Tool Integration & Action Execution.

Covers: the tool registry (custom enterprise tools/API connectors),
intelligent tool selection (rule-based path, since LLM is disabled in
tests), tool invocation + exception/failure handling, and the action
execution accuracy endpoint.
"""


async def test_list_tools_returns_registered_connectors(client):
    resp = await client.get("/api/tools/")
    assert resp.status_code == 200
    tools = resp.json()
    names = {t["name"] for t in tools}
    assert {
        "github_issue_lookup",
        "create_escalation_ticket",
        "query_knowledge_base",
        "restart_service",
        "clear_cache",
    }.issubset(names)
    # Every tool must be self-describing enough for a selector to reason about.
    for t in tools:
        assert t["description"]
        assert isinstance(t["keywords"], list) and len(t["keywords"]) > 0


async def test_selection_picks_restart_service_for_connection_pool_issue(client):
    resp = await client.post(
        "/api/tools/select-and-execute",
        json={"situation": "Incident with database connection pool exhaustion causing timeouts"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["tool_name"] == "restart_service"
    assert body["success"] is True
    assert body["used_llm_selection"] is False  # LLM disabled in test env — proves the fallback path


async def test_selection_picks_escalation_ticket_for_critical_situation(client):
    resp = await client.post(
        "/api/tools/select-and-execute",
        json={
            "situation": "Critical P1 outage, needs to escalate to the human team immediately",
            "severity": "P1",
            "reason": "Unknown root cause",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["tool_name"] == "create_escalation_ticket"
    assert body["success"] is True
    assert "sla_minutes" in body["output"]


async def test_knowledge_base_tool_returns_graceful_failure_when_nothing_found(client):
    """A tool can 'fail' gracefully (no exception, success=False) — this must
    still be recorded, not silently dropped."""
    resp = await client.post(
        "/api/tools/select-and-execute",
        json={
            "situation": "Check knowledge base memory for past history of this exact pattern",
            "key_signature": "nonexistent-service:nonexistent-error",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["tool_name"] == "query_knowledge_base"
    assert body["success"] is False
    assert body["error"] is None  # graceful failure, not an exception


async def test_unrelated_situation_still_returns_a_valid_tool_no_crash(client):
    """Exception/edge-case handling: a situation matching no keywords at all
    must never error out — the selector always returns something usable."""
    resp = await client.post(
        "/api/tools/select-and-execute",
        json={"situation": "Completely unrelated situation with zero matching keywords whatsoever"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["tool_name"] in {
        "github_issue_lookup", "create_escalation_ticket", "query_knowledge_base",
        "restart_service", "clear_cache",
        "semantic_conflict_analyze", "evaluate_code_quality", "semantic_knowledge_search",
    }


async def test_accuracy_endpoint_reflects_executions(client):
    await client.post(
        "/api/tools/select-and-execute",
        json={"situation": "connection pool exhaustion needs restart"},
    )
    await client.post(
        "/api/tools/select-and-execute",
        json={"situation": "knowledge base lookup for past history", "key_signature": "missing:missing"},
    )

    resp = await client.get("/api/tools/accuracy")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_executions"] >= 2
    assert body["overall_accuracy_pct"] is not None
    assert len(body["per_tool"]) >= 1
    for row in body["per_tool"]:
        assert row["total"] >= row["successes"]


async def test_incident_pipeline_uses_intelligent_tool_selection(client):
    """The real incident pipeline (not just the standalone demo endpoint)
    goes through the Tool Selector/Executor now — validate end-to-end."""
    resp = await client.post("/api/incidents/simulate")
    assert resp.status_code == 200
    body = resp.json()
    assert body["anomaly_detected"] is True
    assert "tool_selection_used_llm" in body
    assert body["action_taken"] in {
        "github_issue_lookup", "create_escalation_ticket", "query_knowledge_base",
        "restart_service", "clear_cache",
        "semantic_conflict_analyze", "evaluate_code_quality", "semantic_knowledge_search",
    }
