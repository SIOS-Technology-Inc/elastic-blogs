"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

import os
from typing import Dict
from dotenv import load_dotenv

ELASTICSEARCH_ENDPOINT : str = 'elasticsearch_endpoint'
READ_API_KEY_ENCODED : str = 'read_api_key_encoded'

def load_env_wrapper(verbose:bool=False) -> Dict[str, str]:
    """
    .env ファイルを読み込み、読み込んだ結果を返す。

    Parameters:
        verbose (bool): 読み込み時のデバッグ情報を表示するか? (default=False)
    
    Returns:
        Dict[str, str]: .env ファイルから読み込んだ結果
    """
    my_env: Dict[str, str] = {}

    if load_dotenv(verbose=verbose):
        required_vars = [
            ELASTICSEARCH_ENDPOINT,
            READ_API_KEY_ENCODED
        ]

        for var in required_vars:
            value = os.getenv(var)
            if value is not None:
                my_env[var] = value

    return my_env
