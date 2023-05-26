import logging
import json

logger = logging.getLogger(__name__)


def import_config(file_path):
    try:
        with open(file_path) as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        logger.error(f"Config file not found: {file_path}")
        raise(FileNotFoundError)
    except json.JSONDecodeError:
        logger.error(f"Error parsing JSON file: {file_path}")
        raise(json.JSONDecodeError)