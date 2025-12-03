from pkg.trace_wrapper import traced_method
from .query import *
from internal import model
from internal import interface


class CustDevRepo(interface.ICustDevRepo):
    def __init__(self, tel: interface.ITelemetry, db: interface.IDB):
        self.db = db
        self.tracer = tel.tracer()

    # CustDev operations
    @traced_method()
    async def create_custdev(self, state_id: int, questions_id: int, result: str) -> int:
        args = {
            'state_id': state_id,
            'questions_id': questions_id,
            'result': result,
        }
        custdev_id = await self.db.insert(create_custdev_query, args)
        return custdev_id

    @traced_method()
    async def get_all_custdev(self) -> list[model.CustDev]:
        args = {}
        rows = await self.db.select(get_all_custdev_query, args)
        if rows:
            rows = model.CustDev.serialize(rows)
        return rows

    # CustDevQuestions operations
    @traced_method()
    async def create_questions(self, questions: list[str]) -> int:
        args = {'questions': questions}
        questions_id = await self.db.insert(create_questions_query, args)
        return questions_id

    @traced_method()
    async def create_questions_batch(self, questions_list: list[list[str]]) -> list[int]:
        ids = []
        for questions in questions_list:
            question_id = await self.create_questions(questions)
            ids.append(question_id)
        return ids

    @traced_method()
    async def get_questions_by_id(self, questions_id: int) -> list[model.CustDevQuestions]:
        args = {'questions_id': questions_id}
        rows = await self.db.select(get_questions_by_id_query, args)
        if rows:
            rows = model.CustDevQuestions.serialize(rows)
        return rows

    @traced_method()
    async def get_all_questions(self) -> list[model.CustDevQuestions]:
        rows = await self.db.select(get_all_questions_query, {})
        if rows:
            return model.CustDevQuestions.serialize(rows)
        return []

    @traced_method()
    async def delete_questions(self, questions_id: int) -> None:
        args = {'questions_id': questions_id}
        await self.db.delete(delete_questions_query, args)
