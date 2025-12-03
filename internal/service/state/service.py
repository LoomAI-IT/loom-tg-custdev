from internal import model, interface
from pkg.trace_wrapper import traced_method


class StateService(interface.IStateService):
    def __init__(self, tel: interface.ITelemetry, state_repo: interface.IStateRepo):
        self.tracer = tel.tracer()
        self.logger = tel.logger()
        self.state_repo = state_repo

    @traced_method()
    async def create_state(self, tg_chat_id: int, tg_username: str) -> int:
        state_id = await self.state_repo.create_state(tg_chat_id, tg_username)
        return state_id

    @traced_method()
    async def state_by_id(self, tg_chat_id: int) -> list[model.UserState]:
        state = await self.state_repo.state_by_id(tg_chat_id)
        return state

    @traced_method()
    async def state_by_account_id(self, account_id: int) -> list[model.UserState]:
        state = await self.state_repo.state_by_account_id(account_id)
        return state

    @traced_method()
    async def delete_state_by_tg_chat_id(self, tg_chat_id: int) -> None:
        await self.state_repo.delete_state_by_tg_chat_id(tg_chat_id)