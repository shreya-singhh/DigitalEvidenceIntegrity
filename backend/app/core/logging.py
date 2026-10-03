from pathlib import Path
from loguru import logger as loguru_logger


def configure_logging() -> None:
    logs_dir = Path(__file__).resolve().parents[2] / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    loguru_logger.remove()
    loguru_logger.add(
        logs_dir / "application.log",
        rotation="10 MB",
        retention="10 days",
        level="INFO",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )
    loguru_logger.add(
        "stderr",
        level="INFO",
        colorize=True,
        backtrace=False,
        diagnose=False,
    )


logger = loguru_logger
