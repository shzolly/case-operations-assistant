from backend.app.models import CaseRecord


CASE_DATA = {
    "FM-2026-001": CaseRecord(
        case_id="FM-2026-001",
        case_type="Family",
        status="Pending document review",
        assigned_unit="Family Division - Mercer",
        last_event="Certification filed by respondent",
        days_since_last_event=18,
        flags=["minor-involved", "follow-up-due"],
    ),
    "SC-2026-014": CaseRecord(
        case_id="SC-2026-014",
        case_type="Special Civil",
        status="Awaiting hearing date",
        assigned_unit="Civil Division - Essex",
        last_event="Answer filed",
        days_since_last_event=6,
        flags=[],
    ),
}


def get_case(case_id: str) -> CaseRecord | None:
    return CASE_DATA.get(case_id.upper())

