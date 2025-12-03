from contextvars import ContextVar

import uvicorn
from aiogram import Bot, Dispatcher
import redis.asyncio as redis
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from sulguk import AiogramSulgukMiddleware

from infrastructure.pg.pg import PG
from infrastructure.telemetry.telemetry import Telemetry, AlertManager

from pkg.client.internal.loom_account.client import LoomAccountClient
from pkg.client.internal.loom_authorization.client import LoomAuthorizationClient
from pkg.client.internal.loom_employee.client import LoomEmployeeClient
from pkg.client.internal.loom_organization.client import LoomOrganizationClient
from pkg.client.internal.loom_content.client import LoomContentClient
from pkg.client.external.claude.client import AnthropicClient
from pkg.client.external.telegram.client import LTelegramClient

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
bot = Bot(token=cfg.tg_bot_token)
bot.session.middleware(AiogramSulgukMiddleware())

# Инициализация клиентов
db = PG(tel, cfg.db_user, cfg.db_pass, cfg.db_host, cfg.db_port, cfg.db_name)
anthropic_client = AnthropicClient(
    tel,
    cfg.anthropic_api_key,
    proxy=cfg.proxy
)
state_repo = StateRepo(tel, db)
llm_chat_repo = LLMChatRepo(tel, db)

# Инициализация геттеров
custdev_getter = CustDevGetter(
    tel,
    state_repo,
)

# Инициализация промпт генераторов
create_category_prompt_generator = CreateCategoryPromptGenerator()
train_category_prompt_generator = TrainCategoryPromptGenerator()
create_organization_prompt_generator = CreateOrganizationPromptGenerator()
update_category_prompt_generator = UpdateCategoryPromptGenerator()
update_organization_prompt_generator = UpdateOrganizationPromptGenerator()

create_category_getter = CreateCategoryGetter(
    tel,
    bot,
    anthropic_client,
    create_category_prompt_generator,
    llm_chat_repo,
    state_repo,
    loom_organization_client
)

create_organization_getter = CreateOrganizationGetter(
    tel,
    bot,
    anthropic_client,
    create_organization_prompt_generator,
    llm_chat_repo,
    state_repo
)

update_category_getter = UpdateCategoryGetter(
    tel,
    bot,
    anthropic_client,
    update_category_prompt_generator,
    llm_chat_repo,
    state_repo,
    loom_organization_client,
    loom_content_client,
)

update_organization_getter = UpdateOrganizationGetter(
    tel,
    bot,
    anthropic_client,
    update_organization_prompt_generator,
    llm_chat_repo,
    state_repo,
    loom_organization_client,
)

# Инициализация сервисов
state_service = StateService(tel, state_repo)
intro_service = IntroService(
    tel,
    state_repo,
    llm_chat_repo,
    loom_account_client,
    loom_employee_client,
)
main_menu_service = MainMenuService(
    tel,
    bot,
    state_repo,
    loom_content_client,
)
organization_menu_service = OrganizationMenuService(
    tel,
    state_repo,
    llm_chat_repo,
    loom_employee_client
)
personal_profile_service = PersonalProfileService(
    tel,
)
change_employee_service = ChangeEmployeeService(
    tel,
    bot,
    state_repo,
    loom_employee_client
)

add_employee_service = AddEmployeeService(
    tel,
    state_repo,
    loom_employee_client,
)

content_menu_service = ContentMenuService(
    tel,
    state_repo,
    llm_chat_repo,
    loom_employee_client,
)

generate_publication_service = GeneratePublicationService(
    tel,
    bot,
    state_repo,
    llm_chat_repo,
    loom_content_client,
    loom_employee_client,
    loom_organization_client
)

generate_video_cut_service = GenerateVideoCutService(
    tel,
    state_repo,
    loom_content_client,
)

moderation_publication_service = ModerationPublicationService(
    tel,
    bot,
    state_repo,
    loom_content_client,
    loom_organization_client,
    cfg.domain
)

video_cuts_draft_service = VideoCutsDraftService(
    tel,
    state_repo,
    loom_content_client,
)

draft_publication_service = DraftPublicationService(
    tel,
    bot,
    state_repo,
    loom_content_client,
    loom_organization_client,
    cfg.domain
)

video_cut_moderation_service = VideoCutModerationService(
    tel,
    bot,
    state_repo,
    loom_content_client,
)

add_social_network_service = AddSocialNetworkService(
    tel,
    state_repo,
    loom_content_client,
)

alerts_service = AlertsService(
    tel,
    state_repo,
)

create_category_service = CreateCategoryService(
    tel,
    bot,
    anthropic_client,
    telegram_client,
    create_category_prompt_generator,
    train_category_prompt_generator,
    llm_chat_repo,
    state_repo,
    loom_organization_client,
    loom_content_client
)

create_organization_service = CreateOrganizationService(
    tel,
    bot,
    anthropic_client,
    create_organization_prompt_generator,
    loom_organization_client,
    loom_employee_client,
    loom_content_client,
    llm_chat_repo,
    state_repo
)

update_category_service = UpdateCategoryService(
    tel,
    bot,
    anthropic_client,
    update_category_prompt_generator,
    loom_organization_client,
    loom_content_client,
    telegram_client,
    llm_chat_repo,
    state_repo
)

update_organization_service = UpdateOrganizationService(
    tel,
    bot,
    anthropic_client,
    update_organization_prompt_generator,
    loom_organization_client,
    loom_content_client,
    llm_chat_repo,
    state_repo
)

# Инициализация диалогов
auth_dialog = IntroDialog(
    tel,
    intro_service,
    intro_getter,
)
main_menu_dialog = MainMenuDialog(
    tel,
    main_menu_service,
    main_menu_getter
)
personal_profile_dialog = PersonalProfileDialog(
    tel,
    personal_profile_service,
    personal_profile_getter,
)
organization_menu_dialog = OrganizationMenuDialog(
    tel,
    organization_menu_service,
    organization_menu_getter
)
change_employee_dialog = ChangeEmployeeDialog(
    tel,
    change_employee_service,
    change_employee_getter
)

add_employee_dialog = AddEmployeeDialog(
    tel,
    add_employee_service,
    add_employee_getter,
)

content_menu_dialog = ContentMenuDialog(
    tel,
    content_menu_service,
    content_menu_getter,
)

generate_publication_dialog = GeneratePublicationDialog(
    tel,
    generate_publication_service,
    generate_publication_getter
)

generate_video_cut_dialog = GenerateVideoCutDialog(
    tel,
    generate_video_cut_service,
    generate_video_cut_getter,
)

moderation_publication_dialog = ModerationPublicationDialog(
    tel,
    moderation_publication_service,
    moderation_publication_getter,
)

video_cuts_draft_dialog = VideoCutsDraftDialog(
    tel,
    video_cuts_draft_service,
    video_cuts_draft_getter
)

draft_publication_dialog = DraftPublicationDialog(
    tel,
    draft_publication_service,
    draft_publication_getter,
)

video_cut_moderation_dialog = VideoCutModerationDialog(
    tel,
    video_cut_moderation_service,
    video_cut_moderation_getter,
)

add_social_network_dialog = AddSocialNetworkDialog(
    tel,
    add_social_network_service,
    add_social_network_getter,
)

alerts_dialog = AlertsDialog(
    tel,
    alerts_service,
    alerts_getter,
)

create_category_dialog = CreateCategoryDialog(
    tel,
    create_category_service,
    create_category_getter,
)

create_organization_dialog = CreateOrganizationDialog(
    tel,
    create_organization_service,
    create_organization_getter,
)

update_category_dialog = UpdateCategoryDialog(
    tel,
    update_category_service,
    update_category_getter,
)

update_organization_dialog = UpdateOrganizationDialog(
    tel,
    update_organization_service,
    update_organization_getter,
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
    auth_dialog,
    main_menu_dialog,
    personal_profile_dialog,
    organization_menu_dialog,
    change_employee_dialog,
    add_employee_dialog,
    content_menu_dialog,
    generate_publication_dialog,
    generate_video_cut_dialog,
    moderation_publication_dialog,
    video_cut_moderation_dialog,
    video_cuts_draft_dialog,
    draft_publication_dialog,
    add_social_network_dialog,
    alerts_dialog,
    create_category_dialog,
    create_organization_dialog,
    update_category_dialog,
    update_organization_dialog,
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
