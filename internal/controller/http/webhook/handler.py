from typing import Annotated

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiogram_dialog import BgManagerFactory
from fastapi import Header

from internal import interface
from pkg.log_wrapper import auto_log
from pkg.trace_wrapper import traced_method

class TelegramWebhookController(interface.ITelegramWebhookController):
    def __init__(
            self,
            tel: interface.ITelemetry,
            dp: Dispatcher,
            bot: Bot,
            state_service: interface.IStateService,
            dialog_bg_factory: BgManagerFactory,
            domain: str,
            prefix: str,
            interserver_secret_key: str
    ):
        self.tracer = tel.tracer()
        self.logger = tel.logger()

        self.dp = dp
        self.bot = bot
        self.state_service = state_service
        self.dialog_bg_factory = dialog_bg_factory

        self.domain = domain
        self.prefix = prefix
        self.interserver_secret_key = interserver_secret_key

    @traced_method()
    async def bot_webhook(
            self,
            update: dict,
            x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None
    ):
        if x_telegram_bot_api_secret_token != "secret":
            return {"status": "error", "message": "Wrong secret token !"}

        telegram_update = Update(**update)
        await self.dp.feed_webhook_update(
            bot=self.bot,
            update=telegram_update
        )
        return None

    @auto_log()
    @traced_method()
    async def bot_set_webhook(self):
        await self.bot.set_webhook(
            f'https://{self.domain}{self.prefix}/update',
            secret_token='secret',
            allowed_updates=["message", "callback_query"],
        )

        # Устанавливаем короткое описание бота (показывается под именем)
        await self.bot.set_my_short_description(
            short_description="Хочу услышать вашу историю и опыт. Пару вопросов - и готово!"
        )

        # Устанавливаем полное описание бота (показывается на странице бота)
        await self.bot.set_my_description(
            description=(
                "👋 Привет! Я Loom\n\n"
                "Я помогаю собирать истории и опыт реальных людей.\n\n"
                "Как это работает:\n"
                "💬 Я задам вам несколько вопросов\n"
                "🎯 Вы делитесь своим опытом и мыслями\n"
                "⏱ Это займет всего несколько минут\n"
                "✨ Ваше мнение действительно важно\n\n"
                "Можете отвечать как вам удобно:\n"
                "• Текстом\n"
                "• Голосовым сообщением\n"
                "• Своими словами\n\n"
                "Никаких формальностей - просто расскажите, как есть.\n\n"
                "Нажмите /start чтобы начать!"
            )
        )



