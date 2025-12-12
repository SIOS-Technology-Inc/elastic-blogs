"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

import logging

from llm.cohere.cohere import Cohere
from llm.llm_base import LlmBase
from llm.llm_utils import LlmUtils

from common.env_consts import EnvConsts

logger = logging.getLogger(__name__)

def create_llm_instance(model_id:str, api_key:str, extra_args: dict) -> object:
    """
    LLM のインスタンスを生成する。

    Args:
        model_id (str): The ID of the model to use.
        api_key (str): The API key for the model.
        extra_args (dict): Extra args for the model.

    Returns:
        object: An instance of the LlmBase class.
    """

    llm_instance: LlmBase

    if LlmUtils.is_cohere(model_id):
        llm_instance = Cohere()
    else:
        print(f'Unknown model. : {model_id=}')
    return None

    # 作成した llm_instance に対して、LLMを生成する。
    llm_instance.llm = llm_instance.create_llm(model_id=model_id, api_key=api_key, extra_args=extra_args)

    return llm_instance


def initialize_llm_instance(my_env: dict) -> LlmBase:
    """
    LLM (Large Langurage Model) のインスタンスを初期化する。
    """

    if EnvConsts.LLM_MODEL_ID in my_env and EnvConsts.LLM_API_KEY in my_env:
        llm_instance: LlmBase = create_llm_instance(model_id=my_env[EnvConsts.LLM_MODEL_ID], api_key=my_env[EnvConsts.LLM_API_KEY], extra_args=my_env)
        return llm_instance
    else:
        logger.error('llm_model_id or llm_api_key does not exist in .env.')
        return None
  