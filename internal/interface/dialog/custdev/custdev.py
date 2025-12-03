from typing import Protocol
from abc import abstractmethod

from aiogram.types import Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput

from internal import model


class ICustDevDialog(Protocol):
    @abstractmethod
    def get_dialog(self) -> Dialog:
        pass

    @abstractmethod
    def get_intro_window(self) -> Window:
        pass

    @abstractmethod
    def get_custdev_window(self) -> Window:
        pass


class IDCustDevService(Protocol):
    @abstractmethod
    async def handle_user_message(
            self,
            message: Message,
            widget: MessageInput,
            dialog_manager: DialogManager
    ) -> None:
        pass


class ICustDevGetter(Protocol):
    @abstractmethod
    async def get_hello_data(
            self,
            dialog_manager: DialogManager,
    ) -> dict:
        pass

    @abstractmethod
    async def get_custdev_data(
            self,
            dialog_manager: DialogManager,
    ) -> dict:
        pass


class ICustDevPromptGenerator(Protocol):
    @abstractmethod
    async def get_custdev_system_prompt(self, questions: model.CustDevQuestions) -> str:
        pass
