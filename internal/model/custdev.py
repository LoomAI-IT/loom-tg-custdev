from dataclasses import dataclass
from datetime import datetime


@dataclass
class CustDev:
    id: int
    state_id: int
    questions_id: int
    result: str
    created_at: datetime

    @classmethod
    def serialize(cls, rows) -> list:
        return [
            cls(
                id=row.id,
                state_id=row.state_id,
                questions_id=row.questions_id,
                result=row.result,
                created_at=row.created_at,
            )
            for row in rows
        ]


@dataclass
class CustDevQuestions:
    id: int
    questions: list[str]

    @classmethod
    def serialize(cls, rows) -> list:
        return [
            cls(
                id=row.id,
                questions=row.questions,
            )
            for row in rows
        ]
