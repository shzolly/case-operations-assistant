from backend.app.retrieval import retrieve_policy


EVAL_CASES = [
    {
        "name": "family_follow_up",
        "query": "family case no docket activity missing documents follow-up",
        "expected_prefix": "SOP-FM-001",
    },
    {
        "name": "sensitive_action_approval",
        "query": "official notice external communication supervisor approval",
        "expected_prefix": "SOP-GEN-002",
    },
    {
        "name": "role_permissions",
        "query": "clerk supervisor admin audit permissions tool authorization",
        "expected_prefix": "RBAC-COURT-001",
    },
    {
        "name": "audit_requirements",
        "query": "audit trail request retrieval result tool call final response",
        "expected_prefix": "SOP-AUDIT-004",
    },
]


def test_top_one_retrieval_quality_for_seeded_eval_cases() -> None:
    failures = []
    for case in EVAL_CASES:
        citations = retrieve_policy(case["query"], limit=1)
        actual = citations[0].source_id if citations else "NO_RESULT"
        if not actual.startswith(case["expected_prefix"]):
            failures.append((case["name"], case["expected_prefix"], actual))

    assert failures == []


def test_citations_include_human_readable_excerpts() -> None:
    citations = retrieve_policy("family follow-up missing documents", limit=1)

    assert citations
    assert citations[0].title
    assert "missing documents" in citations[0].excerpt.lower()

