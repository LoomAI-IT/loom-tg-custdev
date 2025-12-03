from internal import interface
from internal.migration.base import Migration, MigrationInfo


class InitialSchemaMigration(Migration):

    def get_info(self) -> MigrationInfo:
        return MigrationInfo(
            version="v0_0_1",
            name="initial_schema",
        )

    async def up(self, db: interface.IDB):
        queries = [
            create_state_table,
        ]

        await db.multi_query(queries)

    async def down(self, db: interface.IDB):
        queries = [
            drop_state_table,
        ]

        await db.multi_query(queries)

create_state_table = """
CREATE TABLE IF NOT EXISTS user_states (
    id SERIAL PRIMARY KEY,
    tg_chat_id BIGINT NOT NULL,
    tg_username TEXT DEFAULT '',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

drop_state_table = """
DROP TABLE IF EXISTS user_states;
"""