from internal import interface
from pkg.trace_wrapper import traced_method

from .model import *


class CustDevController(interface.ICustDevController):
    def __init__(
            self,
            tel: interface.ITelemetry,
            custdev_service: interface.ICustDevService
    ):
        self.tracer = tel.tracer()
        self.logger = tel.logger()
        self.custdev_service = custdev_service

    @traced_method()
    async def create_questions(self, body: CreateQuestionsRequest):
        questions_id = await self.custdev_service.create_questions(body.questions)
        return {"id": questions_id}

    @traced_method()
    async def create_questions_batch(self, body: CreateQuestionsBatchRequest):
        ids = await self.custdev_service.create_questions_batch(body.questions_list)
        return {"ids": ids}

    @traced_method()
    async def get_questions_by_id(self, questions_id: int):
        questions = (await self.custdev_service.get_questions_by_id(questions_id))[0]
        return {
            "id": questions.id,
            "questions": questions.questions
        }

    @traced_method()
    async def get_all_questions(self):
        questions_list = await self.custdev_service.get_all_questions()
        return {
            "questions": [
                {
                    "id": question.id,
                    "questions": question.questions
                }
                for question in questions_list
            ]
        }

    @traced_method()
    async def get_all_custdev(self):
        all_custdev = await self.custdev_service.get_all_custdev()
        return [
            {
                "id": custdev.id,
                "questions": (await self.custdev_service.get_questions_by_id(custdev.questions_id))[0].questions,
                "result": custdev.result
            }
            for custdev in all_custdev
        ]

    @traced_method()
    async def delete_questions(self, questions_id: int):
        await self.custdev_service.delete_questions(questions_id)
        return {"success": True}