from aiogram_dialog import Window, Dialog
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.text import Format, Multi
from sulguk import SULGUK_PARSE_MODE

from internal import interface, model


class CustDevDialog(interface.ICustDevDialog):
    def __init__(
            self,
            tel: interface.ITelemetry,
            custdev_service: interface.IDCustDevService,
            custdev_getter: interface.ICustDevGetter,
    ):
        self.tracer = tel.tracer()
        self.logger = tel.logger()
        self.custdev_service = custdev_service
        self.custdev_getter = custdev_getter

    def get_dialog(self) -> Dialog:
        return Dialog(
            self.get_custdev_window(),
        )

    def get_custdev_window(self) -> Window:
        return Window(
            Multi(
                Format("{message_to_user}"),
            ),

            MessageInput(
                func=self.custdev_service.handle_user_message,
            ),

            state=model.CustdevStates.custdev,
            getter=self.custdev_getter.get_custdev_data,
            parse_mode=SULGUK_PARSE_MODE,
        )
