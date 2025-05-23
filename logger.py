import logging
import os

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

def setup_logger(name, log_file, level=logging.INFO):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

info_logger = setup_logger('info_logger', 'logs/access.log', logging.INFO)
error_logger = setup_logger('error_logger', 'logs/error.log', logging.ERROR)