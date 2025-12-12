"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""
import os

from dotenv import load_dotenv
from common.env_consts import EnvConsts


def load_env_wrapper() -> dict[str, str]:
    """
    .env ファイルを読み込み、読み込んだ結果を返す。

    Returns:
      dict[str, str]: .env ファイルから読み込んだ結果
    """
  
    my_env: dict[str, str] = {}
  
    if load_dotenv(verbose=True):
        required_vars = [
            EnvConsts.ELASTICSEARCH_ENDPOINT,
            EnvConsts.WRITE_API_KEY_ENCODED,
            EnvConsts.READ_API_KEY_ENCODED,
            EnvConsts.LLM_MODEL_ID,
            EnvConsts.LLM_API_KEY
        ]

        for var in required_vars:
            value = os.getenv(var)
            if value is not None:
                my_env[var] = value

    return my_env
