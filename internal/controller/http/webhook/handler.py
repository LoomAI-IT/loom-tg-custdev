from typing import Annotated

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiogram_dialog import BgManagerFactory
from fastapi import Header

from internal import interface, model
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
            short_description="AI SMM инструмент для снижения затрат на рутину. От голосового сообщения до поста в соцсетях за минуты."
        )

        # Устанавливаем полное описание бота (показывается на странице бота)
        await self.bot.set_my_description(
            description=(
                "👋 Добро пожаловать в Loom\n\n"
                "AI SMM инструмент для снижения затрат на рутину.\n\n"
                "Сотрудник говорит голосом:\n"
                "«У нас крутой кейс с клиентом, проект сделали за неделю!»\n\n"
                "Через минуты получаете:\n"
                "✍️ Текст в стиле бренда\n"
                "🎨 Картинку под рубрику\n"
                "📱 Пост для всех соцсетей\n\n"
                "Вместо: ⏱ 2-3 часа работы SMM\n"
                "Получаете: ⚡️ 5 минут на команду\n\n"
                "Нажмите /start чтобы начать!"
            )
        )
