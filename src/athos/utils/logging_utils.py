"""Logging configuration utilities for ATHOS."""

from typing import Any, Dict, Optional, List
import logging
import logging.config
import logging.handlers
import os


def configure_logging(logging_config: Optional[Dict[str, Any]]) -> None:
    """Configure Python logging from a dictionary.

    When ``logging_config`` contains a ``version`` key it is assumed to be a
    full ``logging.config.dictConfig`` specification.  Otherwise a simplified
    schema is expected::

        logging_config:
          level: INFO
          format: "%(message)s"
          handlers:
            - type: console
              level: DEBUG
            - type: file
              filename: "/tmp/athos.log"

    If no ``handlers`` are provided, :func:`logging.basicConfig` is used.
    """

    if not logging_config:
        return

    if "version" in logging_config:
        logging.config.dictConfig(logging_config)
        return

    level = logging_config.get("level")
    fmt = logging_config.get("format")
    handlers_cfg: List[Dict[str, Any]] = logging_config.get("handlers", [])

    if handlers_cfg:
        handlers: Dict[str, Dict[str, Any]] = {}
        handler_names: List[str] = []

        for idx, hcfg in enumerate(handlers_cfg):
            htype = hcfg.get("type", "console")
            name = f"h{idx}"
            handler_names.append(name)

            if htype == "file":
                filename = hcfg.get("filename", "athos.log")
                log_dir = os.path.dirname(filename)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)

                handlers[name] = {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": filename,
                    "maxBytes": hcfg.get("max_bytes", 10485760),
                    "backupCount": hcfg.get("backup_count", 5),
                }
            else:  # console
                handlers[name] = {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                }

            if "level" in hcfg:
                handlers[name]["level"] = hcfg["level"]
            if fmt:
                handlers[name]["formatter"] = "default"

        cfg = {
            "version": 1,
            "handlers": handlers,
            "loggers": {
                "athos": {
                    "level": level or "INFO",
                    "handlers": handler_names,
                    "propagate": False,
                }
            },
            "disable_existing_loggers": False,
        }
        if fmt:
            cfg["formatters"] = {"default": {"format": fmt}}

        logging.config.dictConfig(cfg)
    else:
        logger = logging.getLogger("athos")
        if level:
            logger.setLevel(level)
        handler = logging.StreamHandler()
        if fmt:
            formatter = logging.Formatter(fmt)
            handler.setFormatter(formatter)
        logger.addHandler(handler)
