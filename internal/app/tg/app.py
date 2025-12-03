from aiogram.filters import Command, CommandStart, CommandObject
from aiogram_dialog import setup_dialogs, BgManagerFactory
from aiogram import Dispatcher, Router

from internal import interface


def NewTg(
        dp: Dispatcher,
        command_controller: interface.ICommandController,
        tg_middleware: interface.ITelegramMiddleware,
        custdev_dialog: interface.ICustDevDialog,
) -> BgManagerFactory:
    include_command_handlers(
        dp,
        command_controller
    )
    include_tg_middleware(
        dp,
        tg_middleware,
    )
    dialog_bg_factory = include_dialogs(
        dp,
        custdev_dialog
    )

    return dialog_bg_factory


def include_tg_middleware(
        dp: Dispatcher,
        tg_middleware: interface.ITelegramMiddleware,
):
    dp.update.middleware(tg_middleware.logger_middleware01)


def include_command_handlers(
        dp: Dispatcher,
        command_controller: interface.ICommandController,
):
    dp.message.register(
        command_controller.start_handler,
        CommandStart()
    )


def include_dialogs(
        dp: Dispatcher,
        custdev_dialog: interface.ICustDevDialog
) -> BgManagerFactory:
    dialog_router = Router()
    dialog_router.include_routers(
        custdev_dialog.get_dialog(),
    )

    dp.include_routers(dialog_router)

    dialog_bg_factory = setup_dialogs(dp)

    return dialog_bg_factory
