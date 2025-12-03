from typing import Protocol
from abc import abstractmethod

from internal import model


class ICustDevRepo(Protocol):
    @abstractmethod
    async def create_custdev(self, state_id: int, questions_id: int, result: str) -> int:
        pass

    @abstractmethod
    async def get_custdev_by_state_id(self, state_id: int) -> list[model.CustDev]:
        pass

    @abstractmethod
    async def get_custdev_by_id(self, custdev_id: int) -> list[model.CustDev]:
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


class ICustDevService(Protocol):
    @abstractmethod
    async def create_custdev(self, state_id: int, questions_id: int, result: str) -> int:
        pass

    @abstractmethod
    async def get_custdev_by_state_id(self, state_id: int) -> list[model.CustDev]:
        pass

    @abstractmethod
    async def create_questions(self, questions: list[str]) -> int:
        pass

    @abstractmethod
    async def create_questions_batch(self, questions_list: list[list[str]]) -> list[int]:
        pass

    @abstractmethod
    async def get_questions_by_id(self, questions_id: int) -> model.CustDevQuestions | None:
        pass

    @abstractmethod
    async def get_all_questions(self) -> list[model.CustDevQuestions]:
        pass

    @abstractmethod
    async def delete_questions(self, questions_id: int) -> None:
        pass
