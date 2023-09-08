import logging


def setup_logging():
    log_format = "[%(asctime)s] [%(levelname)s] [%(module)s] - %(message)s"
    file_handler = logging.FileHandler("sbsolver.log", mode="a")
    file_handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
