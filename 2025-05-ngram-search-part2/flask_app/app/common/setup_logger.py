"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

import logging

DEBUG : str = 'DEBUG'
INFO : str = 'INFO'
WARNING : str = 'WARNING'
ERROR : str = 'ERROR'
CRITICAL : str = 'CRITICAL'

# ディフォルトのログレベルを設定
DEFAULT_LOG_LEVEL : str = INFO
# DEFAULT_LOG_LEVEL = 'DEBUG'

# ログのフォーマットを設定
DEFAULT_LOG_FORMAT : str = '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d %(funcName)s %(message)s'
DEFAULT_DATE_FORMAT : str = '[%X]'

def setup_logger(
    logger_name: str, 
    log_level: str = DEFAULT_LOG_LEVEL, 
    log_format: str = DEFAULT_LOG_FORMAT, 
    date_format: str = DEFAULT_DATE_FORMAT
) -> logging.Logger:
    """
    ログの基本設定を行う

    Parameters:
    logger_name (str): ロガー名。
    log_level (str): ログレベルを指定する。デフォルトは 'INFO'。
    log_format (str): ログのフォーマットを指定する。デフォルトは DEFAULT_LOG_FORMAT。
    date_format (str): 日付のフォーマットを指定する。デフォルトは '[%X]'。

    Returns:
    logging.Logger: 設定されたロガーインスタンス。
    """
    if log_level not in [DEBUG, INFO, WARNING, ERROR, CRITICAL]:
        log_level = DEFAULT_LOG_LEVEL

    logger = logging.getLogger(logger_name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))
        logger.addHandler(handler)
        logger.setLevel(log_level)

    return logger
