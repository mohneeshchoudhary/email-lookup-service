from loguru import logger
import sys

def setup_logging(level: str = "INFO"):
    logger.remove()
    logger.add(sys.stderr, level=level.upper(), backtrace=False, diagnose=False,
               format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
                      "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    return logger
