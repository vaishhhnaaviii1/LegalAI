from sqlmodel import Session, select
from app.serializers.ipc_serializer import IPCResponse
from app.models.case_model import Case

from app.services.ai_service import generate_case_summary
from app.services.kanoon_service import search_similar_cases


def create_case_controller(case: Case, session: Session):

    ai_result = generate_case_summary(case.description)
    validated_response = IPCResponse.model_validate(
    ai_result
)

    print("\nVALIDATED RESPONSE\n")
    print(validated_response)

    kanoon_result = search_similar_cases(case.title)

    case.ai_conclusion = ai_result

    session.add(case)
    session.commit()
    session.refresh(case)

    return {
    "validated_sections":
        validated_response.model_dump()
}


def get_cases_controller(session: Session):

    statement = select(Case)

    return session.exec(statement).all()