import traceback

from aiogram import Bot
from aiogram.types import Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput

from internal import interface, model
from pkg.html_validator import validate_html
from pkg.log_wrapper import auto_log
from pkg.tg_action_wrapper import tg_action
from pkg.trace_wrapper import traced_method

from internal.dialog.helpers import StateManager
from internal.dialog.helpers import MessageExtractor

from internal.dialog.custdev.helpers import LLMChatManager


class DCustDevService(interface.IDCustDevService):
    def __init__(
            self,
            tel: interface.ITelemetry,
            bot: Bot,
            anthropic_client: interface.IAnthropicClient,
            custdev_prompt_generator: interface.ICustDevPromptGenerator,
            custdev_service: interface.ICustDevService,
            llm_chat_repo: interface.ILLMChatRepo,
            state_repo: interface.IStateRepo,
            openai_client: interface.IOpenAIClient
    ):
        self.tracer = tel.tracer()
        self.logger = tel.logger()
        self.bot = bot
        self.anthropic_client = anthropic_client
        self.custdev_prompt_generator = custdev_prompt_generator
        self.llm_chat_repo = llm_chat_repo
        self.state_repo = state_repo
        self.openai_client = openai_client
        self.custdev_service = custdev_service

        # Инициализация приватных сервисов
        self.state_manager = StateManager(
            state_repo=self.state_repo
        )
        self.message_extractor = MessageExtractor(
            logger=self.logger,
            bot=self.bot,
            openai_client=self.openai_client
        )
        self.llm_chat_manager = LLMChatManager(
            logger=self.logger,
            bot=self.bot,
            anthropic_client=self.anthropic_client,
            openai_client=self.openai_client,
            custdev_prompt_generator=self.custdev_prompt_generator,
            llm_chat_repo=self.llm_chat_repo,
            custdev_service=self.custdev_service,
        )

    @auto_log()
    @traced_method()
    async def handle_user_message(
            self,
            message: Message,
            widget: MessageInput,
            dialog_manager: DialogManager
    ) -> None:
        state = await self.state_manager.get_state(dialog_manager)
        try:
            self.state_manager.set_show_mode(dialog_manager, send=True)
            chat_id = dialog_manager.dialog_data["chat_id"]
            questions_id = dialog_manager.dialog_data["questions_id"]

            async with tg_action(self.bot, message.chat.id):
                llm_response_json = await self.llm_chat_manager.process_user_message(
                    message=message,
                    chat_id=chat_id,
                    questions_id=questions_id
                )

            if llm_response_json.get("custdev_result"):
                custdev_result = llm_response_json["custdev_result"]

                async with tg_action(self.bot, message.chat.id):
                    _ = await self.custdev_service.create_custdev(
                        state_id=state.id,
                        questions_id=questions_id,
                        result=str(custdev_result)
                    )

                completion_message = (
                    "Спасибо за ваш отзыв!\n\n"
                    "Ваше мнение очень важно для нас и поможет улучшить наш продукт."
                )
                dialog_manager.dialog_data["completion_message"] = completion_message
                await dialog_manager.switch_to(model.CustdevStates.completion)
                return

            message_to_user = llm_response_json["message_to_user"]
            validate_html(message_to_user)
            dialog_manager.dialog_data["message_to_user"] = message_to_user

            await self.llm_chat_manager.save_llm_response(
                chat_id=chat_id,
                llm_response_json=llm_response_json
            )


        except Exception as e:
            await self.bot.send_message(
                state.tg_chat_id,
                "Произошла непредвиденная ошибка, попробуйте продолжить диалог"
            )
            self.logger.error("Ошибка!!!", {"traceback": traceback.format_exc()})