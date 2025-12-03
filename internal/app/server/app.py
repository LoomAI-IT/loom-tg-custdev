from fastapi import FastAPI

from internal import model, interface


def NewServer(
        db: interface.IDB,
        http_middleware: interface.IHttpMiddleware,
        tg_webhook_controller: interface.ITelegramWebhookController,
        custdev_controller: interface.ICustDevController,
        prefix: str,
        environment: str
):
    app = FastAPI(
        openapi_url=prefix + "/openapi.json",
        docs_url=prefix + "/docs",
        redoc_url=prefix + "/redoc",
    )
    include_http_middleware(app, http_middleware)

    include_db_handler(app, db, prefix, environment)
    include_tg_webhook(app, tg_webhook_controller, prefix)
    include_custdev_routes(app, custdev_controller, prefix)

    return app


def include_http_middleware(
        app: FastAPI,
        http_middleware: interface.IHttpMiddleware
):
    http_middleware.logger_middleware02(app)
    http_middleware.trace_middleware01(app)


def include_tg_webhook(
        app: FastAPI,
        tg_webhook_controller: interface.ITelegramWebhookController,
        prefix: str
):
    app.add_api_route(
        prefix + "/update",
        tg_webhook_controller.bot_webhook,
        methods=["POST"]
    )
    app.add_api_route(
        prefix + "/webhook/set",
        tg_webhook_controller.bot_set_webhook,
        methods=["POST"]
    )


def include_db_handler(app: FastAPI, db: interface.IDB, prefix: str, environment: str):
    app.add_api_route(prefix + "/table/create", create_table_handler(db), methods=["GET"])
    app.add_api_route(prefix + "/table/drop", drop_table_handler(db, environment), methods=["GET"])
    app.add_api_route(prefix + "/health", heath_check_handler(), methods=["GET"])


def create_table_handler(db: interface.IDB):
    async def create_table():
        try:
            await db.multi_query(model.create_queries)
        except Exception as err:
            raise err

    return create_table


def heath_check_handler():
    async def heath_check():
        return "ok"

    return heath_check


def drop_table_handler(db: interface.IDB, environment: str):
    async def delete_table():
        if environment == "prod":
            return

        try:
            await db.multi_query(model.drop_queries)
        except Exception as err:
            raise err

    return delete_table


def include_custdev_routes(
        app: FastAPI,
        custdev_controller: interface.ICustDevController,
        prefix: str
):
    app.add_api_route(
        prefix + "/custdev/questions/create",
        custdev_controller.create_questions,
        methods=["POST"]
    )
    app.add_api_route(
        prefix + "/custdev/questions/batch",
        custdev_controller.create_questions_batch,
        methods=["POST"]
    )
    app.add_api_route(
        prefix + "/custdev/questions/{questions_id}",
        custdev_controller.get_questions_by_id,
        methods=["GET"]
    )
    app.add_api_route(
        prefix + "/custdev/questions",
        custdev_controller.get_all_questions,
        methods=["GET"]
    )

    app.add_api_route(
        prefix + "/custdev/all",
        custdev_controller.get_all_custdev,
        methods=["GET"]
    )

    app.add_api_route(
        prefix + "/custdev/questions/{questions_id}",
        custdev_controller.delete_questions,
        methods=["DELETE"]
    )
