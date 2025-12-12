"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

from typing import abstractmethod


class LlmBase:
  """
  LLM関連の基底クラス。
  """
  def __init__(self):
    # コンストラクタは何もしない
    pass

  @abstractmethod
  def create_llm(self, model_id: str, api_key: str) -> object:
        """Creates an LLM instance.

        Args:
            model_id (str): The ID of the LLM to create.
            api_key (str): The API key for accessing the LLM.

        Returns:
            object: An object representing the created LLM instance.
                  It may be a specific class or a reference to an external system.
        """


  @abstractmethod
  def request_to_llm(self, question: str, search_results: list) -> list:
        """Requests to the LLM.

        Args:
            question (str): The user's question.
            search_results (list): The search results that may be used by the LLM.

        Returns:
            list: The response list received from the LLM.
        """


  @abstractmethod
  def extract_answer(self, response: list) -> str:
        """Extracts the answer from a response.

        Args:
            response (str): The response received from the LLM.

        Returns:
            str: The answer part of the response.
        """
