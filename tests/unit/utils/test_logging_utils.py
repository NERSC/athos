import logging
import logging.handlers
from athos.utils.logging_utils import configure_logging


def test_configure_logging_creates_file_directory(tmp_path):
    logfile = tmp_path / "logs" / "athos.log"
    cfg = {
        "level": "INFO",
        "handlers": [
            {"type": "file", "filename": str(logfile)},
        ],
    }

    athos_logger = logging.getLogger("athos")
    for h in list(athos_logger.handlers):
        athos_logger.removeHandler(h)
        h.close()

    configure_logging(cfg)

    assert logfile.parent.exists()
    file_handlers = [h for h in athos_logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
    assert file_handlers
    assert file_handlers[0].baseFilename == str(logfile)

    for h in list(athos_logger.handlers):
        athos_logger.removeHandler(h)
        h.close()


def test_configure_logging_preserves_existing_loggers(tmp_path):
    """Existing loggers should remain enabled after configuration."""
    test_logger = logging.getLogger("athos.test")
    assert not test_logger.disabled

    configure_logging({"level": "INFO", "handlers": [{"type": "console"}]})

    assert not test_logger.disabled
