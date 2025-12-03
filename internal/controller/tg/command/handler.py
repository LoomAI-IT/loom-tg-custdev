from aiogram.types import Message
from aiogram.filters import CommandObject
from aiogram_dialog import DialogManager, StartMode

from internal import model, interface
from pkg.log_wrapper import auto_log
from pkg.trace_wrapper import traced_method


class CommandController(interface.ICommandController):

    def __init__(
            self,
            tel: interface.ITelemetry,
            state_service: interface.IStateService
    ):
        self.logger = tel.logger()
        self.tracer = tel.tracer()
        self.state_service = state_service

    @auto_log()
    @traced_method()
    async def start_handler(
            self,
            message: Message,
            dialog_manager: DialogManager,
            command: CommandObject
    ):
        tg_chat_id = dialog_manager.event.chat.id
        user_state = await self.state_service.state_by_id(tg_chat_id)
        if not user_state:
            tg_username = message.from_user.username if message.from_user.username else "отсутвует username"
            await self.state_service.create_state(tg_chat_id, tg_username)
        start_data = {}
        if command.args:
            start_data["questions_id"] = command.args

        await dialog_manager.start(
            model.CustdevStates.hello,
            mode=StartMode.RESET_STACK,
            data=start_data
        )
