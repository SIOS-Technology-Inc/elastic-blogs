"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

from typing import override

from langchain_cohere import ChatCohere, CohereRagRetriever
from langchain_core.documents import Document
from llm.llm_base import LlmBase


class Cohere(LlmBase):
  """
  Cohere用のクラス
  """
  
  @override
  def create_llm(self, model_id:str, api_key:str, extra_args:dict) -> object:
    # model_id の先頭の '[cohere]' を除いた部分がモデルidとなる。
    return ChatCohere(cohere_api_key=api_key, model=model_id[8:])


  @override
  def request_to_llm(self, question:str, search_results:list) -> list:
    documents = []
    for search_result in search_results:
      # search_result は、Elasticsearch から配列で返ってくるが、
      # 今回のアプリでは、要素数=1の結果しか返さないので、先頭のみ参照する。
      documents.append(Document(page_content=search_result[0]))

    rag = CohereRagRetriever(llm=self.llm, connectors=[])
    response = rag.invoke(input=question, documents=documents)

    return response


  # Cohere の場合、response の最後の要素の page_content に回答が格納されている。
  # なお、出典は、citations に含まれている。
  @override
  def extract_answer(self, response:list) -> str:
    # Return the content of the last element in the response list
    return response[-1].page_content
