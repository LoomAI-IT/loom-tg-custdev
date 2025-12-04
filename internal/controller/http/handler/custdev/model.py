from pydantic import BaseModel


class CreateCustDevRequest(BaseModel):
    state_id: int
    questions_id: int
    result: str


class CreateQuestionsRequest(BaseModel):
    questions: list[str]


class CreateQuestionsBatchRequest(BaseModel):
    questions_list: list[list[str]]