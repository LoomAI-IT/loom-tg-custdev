from internal import model, interface
from pkg.trace_wrapper import traced_method


class CustDevService(interface.ICustDevService):
    def __init__(self, tel: interface.ITelemetry, custdev_repo: interface.ICustDevRepo):
        self.tracer = tel.tracer()
        self.logger = tel.logger()
        self.custdev_repo = custdev_repo

    @traced_method()
    async def create_custdev(self, state_id: int, questions_id: int, result: str) -> int:
        custdev_id = await self.custdev_repo.create_custdev(state_id, questions_id, result)
        return custdev_id

    @traced_method()
    async def create_questions(self, questions: list[str]) -> int:
        questions_id = await self.custdev_repo.create_questions(questions)
        return questions_id

    @traced_method()
    async def create_questions_batch(self, questions_list: list[list[str]]) -> list[int]:
        ids = await self.custdev_repo.create_questions_batch(questions_list)

        return ids

    @traced_method()
    async def get_all_custdev(self) -> list[model.CustDev]:
        return await self.custdev_repo.get_all_custdev()

    @traced_method()
    async def get_custdev_by_id(self, custdev_id: int) -> list[model.CustDev]:
        return await self.custdev_repo.get_custdev_by_id(custdev_id)

    @traced_method()
    async def get_questions_by_id(self, questions_id: int) -> list[model.CustDevQuestions]:
        questions = await self.custdev_repo.get_questions_by_id(questions_id)
        return questions

    @traced_method()
    async def get_all_questions(self) -> list[model.CustDevQuestions]:
        return await self.custdev_repo.get_all_questions()

    @traced_method()
    async def delete_questions(self, questions_id: int) -> None:
        await self.custdev_repo.delete_questions(questions_id)
