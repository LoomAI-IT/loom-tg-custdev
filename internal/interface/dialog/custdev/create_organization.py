from typing import Protocol
from abc import abstractmethod

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button


class ICusDevDialog(Protocol):
    @abstractmethod
    def get_dialog(self) -> Dialog:
        pass

    @abstractmethod
    def get_custdev_window(self) -> Window:
        pass


class ICusDevService(Protocol):
    @abstractmethod
    async def handle_user_message(
            self,
            message: Message,
            widget: MessageInput,
            dialog_manager: DialogManager
    ) -> None:
        pass


class ICusDevGetter(Protocol):
    @abstractmethod
    async def get_custdev_data(
            self,
            dialog_manager: DialogManager,
    ) -> dict:
        pass


class ICusDevPromptGenerator(Protocol):
    @abstractmethod
    async def get_custdev_system_prompt(self, questions_id: int) -> str:
        pass
