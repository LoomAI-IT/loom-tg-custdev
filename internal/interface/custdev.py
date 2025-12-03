from typing import Protocol
from abc import abstractmethod

from internal import model
from internal.controller.http.handler.custdev.model import CreateQuestionsRequest, CreateQuestionsBatchRequest


class ICustDevController(Protocol):

    @abstractmethod
    async def create_questions(self, body: CreateQuestionsRequest) -> dict:
        pass

    @abstractmethod
    async def create_questions_batch(self, body: CreateQuestionsBatchRequest) -> dict:
        pass

    @abstractmethod
    async def get_questions_by_id(self, questions_id: int) -> dict:
        pass

    @abstractmethod
    async def get_all_questions(self) -> dict:
        pass

    @abstractmethod
    async def get_all_custdev(self) -> dict:
        pass

    @abstractmethod
    async def delete_questions(self, questions_id: int) -> dict:
        pass


class ICustDevService(Protocol):
    @abstractmethod
    async def create_custdev(self, state_id: int, questions_id: int, result: str) -> int:
        pass

    @abstractmethod
    async def create_questions(self, questions: list[str]) -> int:
        pass

    @abstractmethod
    async def create_questions_batch(self, questions_list: list[list[str]]) -> list[int]:
        pass

    @abstractmethod
    async def get_questions_by_id(self, questions_id: int) -> list[model.CustDevQuestions]:
        pass

    @abstractmethod
    async def get_all_questions(self) -> list[model.CustDevQuestions]:
        pass

    @abstractmethod
    async def delete_questions(self, questions_id: int) -> None:
        pass

    @abstractmethod
    async def get_all_custdev(self) -> list[model.CustDev]:
        pass



class ICustDevRepo(Protocol):
    @abstractmethod
    async def create_custdev(self, state_id: int, questions_id: int, result: str) -> int:
        pass

    # CustDevQuestions operations
    @abstractmethod
    async def create_questions(self, questions: list[str]) -> int:
        pass

    @abstractmethod
    async def create_questions_batch(self, questions_list: list[list[str]]) -> list[int]:
        pass

    @abstractmethod
    async def get_questions_by_id(self, questions_id: int) -> list[model.CustDevQuestions]:
        pass

    @abstractmethod
    async def get_all_questions(self) -> list[model.CustDevQuestions]:
        pass

    @abstractmethod
    async def delete_questions(self, questions_id: int) -> None:
        pass

    @abstractmethod
    async def get_all_custdev(self) -> list[model.CustDev]:
        pass
