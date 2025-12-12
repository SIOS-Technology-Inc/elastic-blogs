"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

import enum

class LlmUtils(enum.Enum):
  """
  LLM関連のユーティリティクラス(Enum)
  """
  COHERE_COMMAND_R = '[cohere]command-r'
  COHERE_COMMAND_R_08_2024 = '[cohere]command-r-08-2024'
  COHERE_COMMAND_R_PLUS = '[cohere]command-r-plus'
  COHERE_COMMAND_R_PLUS_08_2024 = '[cohere]command-r-plus-08-2024'
  COHERE_COMMAND_R7B = '[cohere]command-r7b-12-2024'

  OLLAMA_ELYZA_SHORTCUT_1_7B = '[ollama]hf.co/mmnga/ELYZA-Shortcut-1.0-Qwen-7B-gguf:Q4_K_M'
  OLLAMA_GEMMA_3_4B = '[ollama]hf.co/unsloth/gemma-3-4b-it-GGUF:Q4_K_M'


  @staticmethod
  def is_cohere(model_id:str):
    """
    Cohere用のモデルIdか?
    """
    return model_id == LlmUtils.COHERE_COMMAND_R.value \
        or model_id == LlmUtils.COHERE_COMMAND_R_08_2024.value \
        or model_id == LlmUtils.COHERE_COMMAND_R_PLUS.value \
        or model_id == LlmUtils.COHERE_COMMAND_R_PLUS_08_2024.value \
        or model_id == LlmUtils.COHERE_COMMAND_R7B.value

  @staticmethod
  def is_ollama(model_id:str):
    """
    Ollama用のモデルIdか?
    """
    return model_id == LlmUtils.OLLAMA_ELYZA_SHORTCUT_1_7B.value \
        or model_id == LlmUtils.OLLAMA_GEMMA_3_4B.value
