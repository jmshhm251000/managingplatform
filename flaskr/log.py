import logging.config
from pythonjsonlogger import jsonlogger


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": "%(asctime)s %(levelname)s %(filename)s %(funcName)s %(message)s",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
        }
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": "/app/logs.log",
            "formatter": "json",
            "level": "DEBUG",
        },
    },
    "root": {
        "handlers": ["file"],
        "level": "DEBUG"
    }
}


logging.config.dictConfig(LOGGING)