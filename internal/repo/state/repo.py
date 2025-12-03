from pkg.trace_wrapper import traced_method
from .query import *
from internal import model
from internal import interface


class StateRepo(interface.IStateRepo):
    def __init__(self, tel: interface.ITelemetry, db: interface.IDB):
        self.db = db
        self.tracer = tel.tracer()

    @traced_method()
    async def create_state(self, tg_chat_id: int, tg_username: str) -> int:
        args = {
            'tg_chat_id': tg_chat_id,
            'tg_username': tg_username,
        }
        state_id = await self.db.insert(create_state, args)
        return state_id

    @traced_method()
    async def state_by_id(self, tg_chat_id) -> list[model.UserState]:
        args = {'tg_chat_id': tg_chat_id}
        rows = await self.db.select(state_by_id, args)
        if rows:
            rows = model.UserState.serialize(rows)
        return rows

    @traced_method()
    async def state_by_account_id(self, account_id) -> list[model.UserState]:
        args = {'account_id': account_id}
        rows = await self.db.select(state_by_account_id, args)
        if rows:
            rows = model.UserState.serialize(rows)

        return rows

    @traced_method()
    async def delete_state_by_tg_chat_id(self, tg_chat_id: int) -> None:
        args = {
            'tg_chat_id': tg_chat_id
        }
        await self.db.delete(delete_state_by_tg_chat_id, args)