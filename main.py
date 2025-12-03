from contextvars import ContextVar

import uvicorn
from aiogram import Bot, Dispatcher
import redis.asyncio as redis
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from sulguk import AiogramSulgukMiddleware

from infrastructure.pg.pg import PG
from infrastructure.telemetry.telemetry import Telemetry, AlertManager

from pkg.client.external.claude.client import AnthropicClient
from pkg.client.external.openai.client import OpenAIClient

from internal.controller.http.middlerware.middleware import HttpMiddleware
from internal.controller.tg.middleware.middleware import TgMiddleware

from internal.controller.tg.command.handler import CommandController
from internal.controller.http.webhook.handler import TelegramWebhookController

from internal.dialog.custdev.dialog import CustDevDialog

from internal.service.state.service import StateService
from internal.service.custdev.service import CustDevService
from internal.dialog.custdev.service import DCustDevService

from internal.dialog.custdev.getter import CustDevGetter

from internal.dialog.custdev.prompt import CustDevPromptGenerator

from internal.repo.state.repo import StateRepo
from internal.repo.custdev.repo import CustDevRepo
from internal.repo.llm_chat.repo import LLMChatRepo

from internal.app.tg.app import NewTg
from internal.app.server.app import NewServer

from internal.config.config import Config

cfg = Config()

# Инициализация мониторинга
alert_manager = AlertManager(
    cfg.alert_tg_bot_token,
    cfg.service_name,
    cfg.alert_tg_chat_id,
    cfg.alert_tg_chat_thread_id,
    cfg.grafana_url,
    cfg.monitoring_redis_host,
    cfg.monitoring_redis_port,
    cfg.monitoring_redis_db,
    cfg.monitoring_redis_password
)

log_context: ContextVar[dict] = ContextVar('log_context', default={})

tel = Telemetry(
    cfg.log_level,
    cfg.root_path,
    cfg.environment,
    cfg.service_name,
    cfg.service_version,
    cfg.otlp_host,
    cfg.otlp_port,
    log_context,
    alert_manager
)

redis_client = redis.Redis(
    host=cfg.monitoring_redis_host,
    port=cfg.monitoring_redis_port,
    password=cfg.monitoring_redis_password,
    db=2
)
key_builder = DefaultKeyBuilder(with_destiny=True)
storage = RedisStorage(
    redis=redis_client,
    key_builder=key_builder
)
dp = Dispatcher(storage=storage)
bot = Bot(token=cfg.tg_custdev_bot_token)
bot.session.middleware(AiogramSulgukMiddleware())

# Инициализация клиентов
db = PG(tel, cfg.db_user, cfg.db_pass, cfg.db_host, cfg.db_port, cfg.db_name)
anthropic_client = AnthropicClient(
    tel,
    cfg.anthropic_api_key,
    proxy=cfg.proxy
)
openai_client = OpenAIClient(
    tel,
    cfg.openai_api_key,
    neuroapi_api_key="",
    proxy=cfg.proxy
)
state_repo = StateRepo(tel, db)
llm_chat_repo = LLMChatRepo(tel, db)
custdev_repo = CustDevRepo(tel, db)

# Инициализация промпт генераторов
custdev_prompt_generator = CustDevPromptGenerator()

# Инициализация сервисов
state_service = StateService(tel, state_repo)
custdev_service = CustDevService(tel, custdev_repo)

# Инициализация геттеров
custdev_getter = CustDevGetter(
    tel,
    bot,
    anthropic_client,
    custdev_service,
    custdev_prompt_generator,
    llm_chat_repo,
    state_repo,
)

# Инициализация диалог-сервисов
dcustdev_service = DCustDevService(
    tel,
    bot,
    anthropic_client,
    custdev_prompt_generator,
    custdev_service,
    llm_chat_repo,
    state_repo,
    openai_client
)

# Инициализация диалогов
custdev_dialog = CustDevDialog(
    tel,
    dcustdev_service,
    custdev_getter,
)

command_controller = CommandController(tel, state_service)

tg_middleware = TgMiddleware(
    tel,
    state_service,
    bot,
    log_context
)

dialog_bg_factory = NewTg(
    dp,
    command_controller,
    tg_middleware,
    custdev_dialog,
)
tg_middleware.dialog_bg_factory = dialog_bg_factory

# Инициализация middleware
http_middleware = HttpMiddleware(
    tel,
    cfg.prefix,
    log_context
)
tg_webhook_controller = TelegramWebhookController(
    tel,
    dp,
    bot,
    state_service,
    dialog_bg_factory,
    cfg.domain,
    cfg.prefix,
    cfg.interserver_secret_key
)

app = NewServer(
    db,
    http_middleware,
    tg_webhook_controller,
    cfg.prefix,
    cfg.environment
)

if __name__ == "__main__":
    if cfg.environment == "prod":
        workers = 1
    else:
        workers = 1

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(cfg.http_port),
        workers=workers,
        loop="uvloop",
        access_log=False,
    )
