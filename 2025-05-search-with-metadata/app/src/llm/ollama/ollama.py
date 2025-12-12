"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

from typing import override
import logging
import ollama

from common.env_consts import EnvConsts

from llm.llm_consts import LlmConsts
from llm.llm_base import LlmBase


logger = logging.getLogger(__name__)

class Ollama(LlmBase):
  """
  Ollama用のクラス
  """
  model_id: str = ""
  llm = ollama
  ollama_url: str = ""
  
  @override
  def create_llm(self, model_id: str, api_key: str, extra_args: dict) -> object:
    # model_id の先頭の '[ollama]' を除いた部分がモデルidとなる。
    self.model_id = model_id[8:]
    self.ollama_url = extra_args.get(EnvConsts.OLLAMA_URL, 'http://localhost:11434')
    logger.debug(f'{self.model_id=}')
    return self.llm


  # LLM に問い合わせる。
  @override
  def request_to_llm(self, question:str, search_results:list) -> list:
    contexts=""
    for i, search_result in enumerate(search_results):
      # search_result は、Elasticsearch から配列で返ってくるが、
      # 今回のアプリでは、要素数=1の結果しか返さないので、先頭のみ参照する。
      # ※注 サニタイジングは行っていません。
      contexts += f"<context{i}>{search_result[0]}</context{i}>\n"

    content = f"""
### 指示:

以下の contexts をもとにして question に回答してください。
contexts に情報が含まれていない場合は、「わかりません。」と回答してください。

<contexts>
{contexts}
</contexts>

<question>
{question}
</question>

### 応答:
"""

    logger.debug(f"{content=}")

    client = ollama.Client(host=self.ollama_url)

    response = client.chat(model=self.model_id,
      messages=[{LlmConsts.ROLE: LlmConsts.USER, LlmConsts.CONTENT: content}])

    return response


  # Ollama の場合、ChatResponse の message の content に回答が格納されている。
  # Ollama の場合、ディフォルトでは回答の出典(citations)は含まれていない。(そういうリクエストを書く必要がある)
  @override
  def extract_answer(self, response:list) -> str:
    if LlmConsts.MESSAGE in response:
      message = response[LlmConsts.MESSAGE]

      if type(message) is ollama._types.Message:
        return message.content

      return message

    return 'Not Found'
