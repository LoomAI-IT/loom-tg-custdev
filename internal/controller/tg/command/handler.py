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
            state_service: interface.IStateService,
            llm_chat_repo: interface.ILLMChatRepo
    ):
        self.logger = tel.logger()
        self.tracer = tel.tracer()
        self.state_service = state_service
        self.llm_chat_repo = llm_chat_repo

    @auto_log()
    @traced_method()
    async def start_handler(
            self,
            message: Message,
            dialog_manager: DialogManager,
            command: CommandObject
    ):
        tg_chat_id = dialog_manager.event.chat.id
        tg_username = dialog_manager.event.from_user.username

        user_state = await self.state_service.state_by_id(tg_chat_id)
        if not user_state:
            await self.state_service.create_state(tg_chat_id, tg_username)
            user_state = await self.state_service.state_by_id(tg_chat_id)
        user_state = user_state[0]

        start_data = {}
        if command.args:
            start_data["questions_id"] = command.args

        chat = (await self.llm_chat_repo.get_chat_by_state_id(user_state.id))[0]
        await self.llm_chat_repo.delete_chat(chat.id)

        await dialog_manager.start(
            model.CustdevStates.hello,
            mode=StartMode.RESET_STACK,
            data=start_data
        )
