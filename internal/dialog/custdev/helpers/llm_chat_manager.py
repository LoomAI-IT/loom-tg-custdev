from aiogram import Bot
from aiogram.types import Message
from aiogram_dialog import DialogManager

from internal import interface
from internal.dialog.helpers import MessageExtractor

from pkg.html_validator import validate_html


class LLMChatManager:
    def __init__(
            self,
            logger,
            bot: Bot,
            anthropic_client: interface.IAnthropicClient,
            custdev_service: interface.ICustDevService,
            custdev_prompt_generator: interface.ICustDevPromptGenerator,
            llm_chat_repo: interface.ILLMChatRepo,
            openai_client: interface.IOpenAIClient,
    ):
        self.logger = logger
        self.bot = bot
        self.anthropic_client = anthropic_client
        self.custdev_service = custdev_service
        self.custdev_prompt_generator = custdev_prompt_generator
        self.llm_chat_repo = llm_chat_repo

        self.message_extractor = MessageExtractor(
            logger=self.logger,
            bot=self.bot,
            openai_client=openai_client,
        )

    async def process_user_message(
            self,
            dialog_manager: DialogManager,
            message: Message,
            chat_id: int,
            questions_id: int,
    ) -> dict:
        user_text = await self.message_extractor.process_voice_or_text_input(
            dialog_manager=dialog_manager,
            message=message,
        )

        message_to_llm = f"""
<user>
{user_text}
</user>
"""
        await self.llm_chat_repo.create_message(
            chat_id=chat_id,
            role="user",
            text=f'{{"message_to_llm": {message_to_llm}}}'
        )

        llm_response_json, generate_cost = await self.get_llm_response(
            chat_id=chat_id,
            enable_web_search=True,
            questions_id=questions_id,
        )

        return llm_response_json

    async def save_llm_response(
            self,
            chat_id: int,
            llm_response_json: dict
    ) -> None:
        await self.llm_chat_repo.create_message(
            chat_id=chat_id,
            role="assistant",
            text=str(llm_response_json)
        )

    async def get_llm_response(
            self,
            chat_id: int,
            questions_id: int,
            max_tokens: int = 15000,
            thinking_tokens: int = 10000,
            enable_web_search: bool = False,
    ) -> tuple[dict, dict]:
        messages = await self.llm_chat_repo.get_all_messages(chat_id)
        history = []
        for msg in messages:
            history.append({
                "role": msg.role,
                "content": msg.text
            })

        questions = (await self.custdev_service.get_questions_by_id(questions_id))[0]
        system_prompt = await self.custdev_prompt_generator.get_custdev_system_prompt(questions)
        llm_response_json, generate_cost = await self.anthropic_client.generate_json(
            history=history,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            thinking_tokens=thinking_tokens,
            enable_web_search=enable_web_search,
        )

        if llm_response_json.get("message_to_user"):
            try:
                validate_html(llm_response_json["message_to_user"])
            except Exception as e:
                self.logger.warning("LLM сгенерировала невалидный HTML", {"error": str(e)})
                llm_response_json, generate_cost = await self.anthropic_client.generate_json(
                    history=history,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    thinking_tokens=thinking_tokens,
                    enable_web_search=enable_web_search,
                    llm_model="claude-haiku-4-5-20251001"
                )

        return llm_response_json, generate_cost
