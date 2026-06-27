import logging

logging.basicConfig(
    level=logging.INFO,
    format= "%(asctime)s, %(levelname)s, " "%(funcName)s, %(lineno)d, %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("TaskEnergySystem")
