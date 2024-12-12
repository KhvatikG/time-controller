from loguru import logger


def logger_setup() -> None:
    logger.add(
        "logs/log_{time:%Y-%m-%d}.log",
        rotation="23:55",
        retention="10 days",
        compression="zip",
    )
    logger.add(
        "logs/aiogram_events_{time:%Y-%m-%d}.log",
        rotation="23:55",
        retention="10 days",
        compression="zip",
        filter=lambda record: "aiogram_event" in record["extra"]
    )


