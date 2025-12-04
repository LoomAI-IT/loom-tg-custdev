create_state_table = """
CREATE TABLE IF NOT EXISTS user_states (
    id SERIAL PRIMARY KEY,
    tg_chat_id BIGINT NOT NULL,
    tg_username TEXT DEFAULT '',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

create_llm_chat_table = """
CREATE TABLE IF NOT EXISTS llm_chats (
    id SERIAL PRIMARY KEY,
    state_id INTEGER NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

create_llm_message_table = """
CREATE TABLE IF NOT EXISTS llm_messages (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    text TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

create_custdev_questions_table = """
CREATE TABLE IF NOT EXISTS custdev_questions (
    id SERIAL PRIMARY KEY,
    questions TEXT[] NOT NULL
);
"""

create_custdev_table = """
CREATE TABLE IF NOT EXISTS custdev (
    id SERIAL PRIMARY KEY,
    state_id INTEGER NOT NULL,
    questions_id INTEGER NOT NULL,
    result TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

drop_state_table = """
DROP TABLE IF EXISTS user_states;
"""

drop_llm_chat_table = """
DROP TABLE IF EXISTS llm_chats;
"""

drop_llm_message_table = """
DROP TABLE IF EXISTS llm_messages;
"""

drop_custdev_questions_table = """
DROP TABLE IF EXISTS custdev_questions;
"""

drop_custdev_table = """
DROP TABLE IF EXISTS custdev;
"""

create_queries = [
    create_state_table,
    create_llm_chat_table,
    create_llm_message_table,
    create_custdev_questions_table,
    create_custdev_table,
]

drop_queries = [
    drop_custdev_table,
    drop_custdev_questions_table,
    drop_llm_message_table,
    drop_llm_chat_table,
    drop_state_table,
]