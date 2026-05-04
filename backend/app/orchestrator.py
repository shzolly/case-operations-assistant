from backend.app.models import AssistantResponse, UserContext
from backend.app.workflow import run_case_workflow


def answer_case_question(question: str, user: UserContext) -> AssistantResponse:
    return run_case_workflow(question, user)
