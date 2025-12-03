import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("vin_cli")
logger.setLevel(logging.DEBUG)
# Log file rotates at 1MB, keeps 5 backups 
handler = RotatingFileHandler("vin_cli.log", maxBytes=1_000_000, backupCount=5)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
