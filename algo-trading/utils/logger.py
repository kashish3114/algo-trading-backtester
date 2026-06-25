"""
logging setup. console + file, both using the same format. import
get_logger(__name__) in every module instead of calling logging directly.
"""

import logging
import os
import sys

# need this so config is importable no matter where this gets run from
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_CONFIGURED = False


def _configure_root_logger():
    # only run this once, otherwise we'd attach duplicate handlers and every
    # log line would print twice (learned that the hard way)
    global _CONFIGURED
    if _CONFIGURED:
        return

    try:
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

        # console only needs INFO+, DEBUG spam isn't useful to stare at live
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # but the file gets everything, in case we need to dig later
        log_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", config.LOG_FILE)
        )
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

        _CONFIGURED = True
    except Exception as exc:
        # if logging itself breaks, don't take the whole app down with it
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
        print(f"Warning: failed to configure file logging ({exc}). Using basicConfig fallback.")


def get_logger(module_name):
    # just pass __name__ from wherever you're calling this
    _configure_root_logger()
    return logging.getLogger(module_name)
