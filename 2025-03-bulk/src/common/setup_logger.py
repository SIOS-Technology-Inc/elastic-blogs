"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

import logging

# ディフォルトのログレベルを設定
DEFAULT_LOG_LEVEL = 'INFO'
# DEFAULT_LOG_LEVEL = 'DEBUG'

# ログのフォーマットを設定
DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d %(funcName)s %(message)s"


def setup_logger(logger_name: str, log_level: str = DEFAULT_LOG_LEVEL) -> logging.Logger:
    """
    ログの基本設定を行う

    Parameters:
    logger_name (str): ロガー名。
    log_level (str): ログレベルを指定する。デフォルトは 'INFO'。

    Returns:
    logging.Logger: 設定されたロガーインスタンス。
    """
    if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        log_level = DEFAULT_LOG_LEVEL

    logging.basicConfig(
        level=log_level,
        format=DEFAULT_LOG_FORMAT,
        datefmt="[%X]"
    )
    return logging.getLogger(logger_name)
