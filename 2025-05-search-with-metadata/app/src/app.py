"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License

検索画面またはRAGの質問画面を表示する。

Usage:
  検索画面を表示する場合（デフォルト）
    streamlit.cmd run src/app.py search
  RAGの質問画面を表示する場合
    streamlit.cmd run src/app.py rag
"""

import sys

import streamlit as st

from elasticsearch import Elasticsearch

from common.st_session_consts import StSessionConsts
from common.load_env_wrapper import load_env_wrapper
from common.setup_logger import setup_logger
from common.ui_mode import UiMode

from elastic.es_func import initialize_es, create_search_params, es_search_template

from llm.llm_base import LlmBase
from llm.llm_consts import LlmConsts
from llm.llm_wrapper import initialize_llm_instance


logger = setup_logger(__name__)

def search(es_client:Elasticsearch, query:str, fiscal_year:str) -> list:
  """
  Elasticsearch に検索処理を依頼し、検索結果を受け取る。
  """

  tmp_fiscal_year = fiscal_year

  # year: すべて　の場合は、事業年度によるフィルタリングを行わない。
  if tmp_fiscal_year == 'すべて':
    tmp_fiscal_year = ''

  # 検索用パラメタを生成する。
  search_params: dict = create_search_params(query, tmp_fiscal_year)

  # 検索テンプレートを使って検索する。
  search_results: list = es_search_template(es_client, search_params)

  # for debug (検索結果)
  logger.debug('----- 検索結果 -----')
  for i, results in enumerate(search_results):
    logger.debug(f'{i}')
    for sub_result in results:
      logger.debug(f'{sub_result}')

  return search_results


def search_onclick():
  """
  検索ボタンが押されたときに実行される処理
  """
  # 1. ユーザーからの質問を受けとる。
  query = st.session_state[StSessionConsts.QUERY]
  st.write(query)

  # 2. Elasticsearch へ問い合わせ / 3.検索結果の受け取り
  es_client = st.session_state[StSessionConsts.ES_CLIENT]
  fiscal_year = st.session_state[StSessionConsts.FISCAL_YEAR]

  search_results = search(es_client, query, fiscal_year)
  
  # 4. 検索結果の表示
  for i, results in enumerate(search_results):
    st.write(f'{i}')
    for sub_result in results:
      st.markdown(f'{sub_result}')


def question_to_llm(question, search_results) -> str:
  """
  検索結果を情報源として LLM に質問し、回答を受け取る。
  """
  
  # LLM に問い合わせる。
  llm_instance: LlmBase = st.session_state[StSessionConsts.LLM_INSTANCE]
  response = llm_instance.request_to_llm(question=question, search_results=search_results)

  # for debug (LLMの結果)
  logger.debug('----- LLMからのレスポンス -----')
  for r in response:
    logger.debug(r)

  answer = llm_instance.extract_answer(response=response)

  return answer


def create_fiscal_year_radio(st):
  return st.sidebar.radio(
    label = '事業年度',
    options = ['すべて', '2024年12月期', '2023年12月期', '2022年12月期', '2021年12月期', '2020年12月期', '2019年12月期', '2018年12月期']
  )


def show_rag_ui(prompt_to_user:str = ''):
  """
  RAG (Retrieval-Augmented Generation) 用の UI を表示する。
  """
  
  if prompt_to_user == '':
    prompt_to_user = '質問を入力してください。'
  st.set_page_config(page_title='有価証券報告書検索 RAG')
  st.title('有価証券報告書検索 RAG')

  fiscal_year = create_fiscal_year_radio(st)

  st.session_state[StSessionConsts.FISCAL_YEAR] = fiscal_year
  logger.debug(f'{st.session_state[StSessionConsts.FISCAL_YEAR]=}')

  if StSessionConsts.MESSAGES not in st.session_state.keys():
    st.session_state.messages = [{LlmConsts.ROLE: LlmConsts.ASSISTANT, LlmConsts.CONTENT: prompt_to_user}]

  # Display chat messages
  for message in st.session_state.messages:
    with st.chat_message(message[LlmConsts.ROLE]):
      st.write(message[LlmConsts.CONTENT])

  # 1. ユーザーからの質問を受け付ける。
  if query := st.chat_input():
    with st.chat_message(LlmConsts.USER):
      st.write(query)
    st.session_state.messages.append({LlmConsts.ROLE: LlmConsts.USER, LlmConsts.CONTENT: query})

    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1][LlmConsts.ROLE] != LlmConsts.ASSISTANT:
      with st.chat_message(LlmConsts.ASSISTANT):
        with st.spinner('Thinking...'):
          # 2. Elasticsearch へ問い合わせ / 3.検索結果の受け取り
          fiscal_year = st.session_state[StSessionConsts.FISCAL_YEAR]
          es_client = st.session_state[StSessionConsts.ES_CLIENT]
          search_results = search(es_client, query, fiscal_year)

          # 4. LLM へ問い合わせ / 5. 回答結果の受け取り
          answer = question_to_llm(query, search_results)

          # 6. 回答結果の表示
          st.markdown(answer)

          message = {LlmConsts.ROLE: LlmConsts.ASSISTANT, LlmConsts.CONTENT: answer}
          st.session_state.messages.append(message)


def show_search_ui():
  """
  検索用の UI を表示する。
  """

  st.set_page_config(page_title='有価証券報告書検索')
  st.title('有価証券報告書検索')
  st.text_input(label='クエリ', key=StSessionConsts.QUERY)
  st.button(label='検索', on_click=search_onclick)

  fiscal_year = create_fiscal_year_radio(st)

  st.session_state[StSessionConsts.FISCAL_YEAR] = fiscal_year
  logger.debug(f'{st.session_state[StSessionConsts.FISCAL_YEAR]=}')


def show_ui(mode:UiMode, prompt_to_user:str = ''):
  """
  UI を表示する。モードに応じて RAG または検索画面を表示する。
  """
  
  if UiMode.is_rag(mode):
    show_rag_ui(prompt_to_user)
  else:
    show_search_ui()


# --- main ---
if __name__ == '__main__':
  my_env : dict[str, str] = load_env_wrapper()

  logger.debug(f'{my_env=}')

  mode_str: str = UiMode.SEARCH

  args: list[str] = sys.argv

  logger.debug(f'{len(args)=}')

  if len(args) > 1:
    mode_str = args[1]
    logger.debug(f'{mode_str=}')

  ui_mode: UiMode = UiMode.parse_mode(mode_str)
  logger.debug(f'{ui_mode=}')

  es_client: Elasticsearch

  if StSessionConsts.ES_CLIENT in st.session_state:
    es_client = st.session_state[StSessionConsts.ES_CLIENT]
  else:
    es_client = initialize_es(my_env)
    if es_client is None:
      print('es_client is null.')
      sys.exit(1)

    st.session_state[StSessionConsts.ES_CLIENT] = es_client
    logger.debug(f"{es_client.info()}")


  if UiMode.is_rag(ui_mode):
    if StSessionConsts.LLM_INSTANCE in st.session_state:
      llm_instance = st.session_state[StSessionConsts.LLM_INSTANCE]
    else:
      llm_instance = initialize_llm_instance(my_env)
      if llm_instance is None:
        print("Failed to create llm_instance")
        sys.exit(1)

      st.session_state[StSessionConsts.LLM_INSTANCE] = llm_instance
      logger.debug(f"{llm_instance=}")

  show_ui(ui_mode)
