import atexit
import logging
import logging.config
import logging.handlers
from pathlib import Path
import json
import os


def setup_logging() -> None:

    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = Path(
        os.path.join(current_dir, "logging_configs", "config_prod.json")
    )  # PICK TEST OR PROD BASED ON ENUM ENVIROMENT PARAMETER VARIABLE
    with open(config_file) as f:
        config = json.load(f)
    logging.config.dictConfig(config)

    queue_handler = logging.getHandlerByName(
        "queue_handler"
    )  # this is to make running of the different handlers asynchronous

    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)


def get_logger(name: str) -> str:
    return logging.getLogger(name)
