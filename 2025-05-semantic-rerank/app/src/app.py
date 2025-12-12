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

from common.env_consts import EnvConsts
from common.st_consts import StConsts
from common.load_env_wrapper import load_env_wrapper
from common.setup_logger import setup_logger
from common.ui_mode import UiMode
from elastic.es_func import initialize_es, create_search_params, es_search_template
from elastic.kakinosuke_consts import KakinosukeConsts
from llm.llm_base import LlmBase
from llm.llm_consts import LlmConsts
from llm.llm_wrapper import initialize_llm_instance


logger = setup_logger(__name__)

def get_session_state_value(key: str, default_value: str) -> str:
    """
    Retrieves a value from the session state, or returns a default value if not found.
    """
    return st.session_state.get(key, default_value)


def search(es_client:Elasticsearch, query:str, ui_mode:UiMode, rerank_mode:str) -> list:
    """
    Elasticsearch に検索処理を依頼し、検索結果を受け取る。
    """

    search_template_id: str
    if rerank_mode == StConsts.DO:
        search_template_id = KakinosukeConsts.SEARCH_TEMPLATE_ID_WITH_RERANK
    else:
        search_template_id = KakinosukeConsts.SEARCH_TEMPLATE_ID_WITHOUT_RERANK

    # 検索用パラメタを生成する。
    highlight: bool = not UiMode.is_rag(ui_mode)

    search_params: dict = create_search_params(query, highlight)

    # 検索テンプレートを使って検索する。
    search_results: list = es_search_template(es_client, search_params, search_template_id)

    # for debug (検索結果)
    logger.debug('----- 検索結果 -----')
    for i, results in enumerate(search_results):
        logger.debug(f'{i}')
        for sub_result in results:
            logger.debug(f'{sub_result}')

    return search_results


def search_onclick() -> None:
    """
    検索ボタンが押されたときに実行される処理
    """
    # 1. ユーザーからの質問を受けとる。
    # query = st.session_state.get(StConsts.SESSION_KEY_QUERY)
    query = get_session_state_value(StConsts.SESSION_KEY_QUERY, '')
    st.write(query)

    # 2. Elasticsearch へ問い合わせ / 3.検索結果の受け取り
    # es_client = st.session_state.get(StConsts.SESSION_KEY_ES_CLIENT)
    es_client : Elasticsearch = get_session_state_value(StConsts.SESSION_KEY_ES_CLIENT)
  
    # rerank_mode = st.session_state.get(StConsts.SESSION_KEY_RERANK_MODE, StConsts.NOT_DO)
    rerank_mode = get_session_state_value(StConsts.SESSION_KEY_RERANK_MODE, StConsts.NOT_DO)

    # 検索用パラメタを生成する。
    search_results = search(es_client, query, UiMode.SEARCH, rerank_mode)
  
    # 4. 検索結果の表示
    for i, results in enumerate(search_results):
        st.write(f'{i}')
        for sub_result in results:
            st.write(f'{sub_result}', unsafe_allow_html=True)


def question_to_llm(question: str, search_results: list) -> str:
    """
    検索結果を情報源として LLM に質問し、回答を受け取る。
    """
  
    # LLM に問い合わせる。
    # llm_instance: LlmBase = st.session_state.get(StConsts.SESSION_KEY_LLM_INSTANCE)
    llm_instance: LlmBase = get_session_state_value(StConsts.SESSION_KEY_LLM_INSTANCE)
    response = llm_instance.request_to_llm(question=question, search_results=search_results)

    # for debug (LLMの結果)
    logger.debug('----- LLMからのレスポンス -----')
    for r in response:
        logger.debug(r)

    answer = llm_instance.extract_answer(response=response)

    return answer


def create_rerank_mode_radio(st: streamlit) -> str:
    """
    Creates a sidebar radio button for selecting the rerank mode.
    """
    rerank_mode = st.sidebar.radio(
        label = StConsts.SEMANTIC_RERANK,
        options = [StConsts.NOT_DO, StConsts.DO]
    )

    logger.debug(f"Rerank mode: {rerank_mode}")

    return rerank_mode


def display_chat_messages(messages: list[dict]) -> None:
    for message in messages:
        with st.chat_message(message[LlmConsts.ROLE]):
            st.write(message[LlmConsts.CONTENT])


def handle_user_query(query: str) -> None:
    with st.chat_message(LlmConsts.USER):
        st.write(query)
    st.session_state.messages.append({LlmConsts.ROLE: LlmConsts.USER, LlmConsts.CONTENT: query})

    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1][LlmConsts.ROLE] != LlmConsts.ASSISTANT:
        with st.chat_message(LlmConsts.ASSISTANT):
            with st.spinner('Thinking...'):
                # 2. Elasticsearch へ問い合わせ / 3.検索結果の受け取り
                # rerank_mode = st.session_state.get(StConsts.SESSION_KEY_RERANK_MODE, StConsts.NOT_DO)
                rerank_mode = get_session_state_value(StConsts.SESSION_KEY_RERANK_MODE, StConsts.NOT_DO)

                # es_client = st.session_state.get(StConsts.SESSION_KEY_ES_CLIENT)
                es_client = get_session_state_value(StConsts.SESSION_KEY_ES_CLIENT)
                search_results = search(es_client, query, UiMode.RAG, rerank_mode)

                # 4. LLM へ問い合わせ / 5. 回答結果の受け取り
                answer = question_to_llm(query, search_results)

                # 6. 回答結果の表示
                st.markdown(answer)

                message = {LlmConsts.ROLE: LlmConsts.ASSISTANT, LlmConsts.CONTENT: answer}
                st.session_state.messages.append(message)


def setup_page(st: streamlit, title: str) -> None:
    """
    Sets up the Streamlit page with the given title.
    """
    st.set_page_config(page_title=title)
    st.title(title)


def show_rag_ui(prompt_to_user:str = StConsts.DEFAULT_PROMPT) -> None:
    """
    RAG (Retrieval-Augmented Generation) 用の UI を表示する。
    """
  
    setup_page(st, StConsts.PAGE_TITLE_RAG)


    st.session_state[StConsts.SESSION_KEY_RERANK_MODE] = create_rerank_mode_radio(st)

    if StConsts.SESSION_KEY_MESSAGES not in st.session_state.keys():
        st.session_state.messages = [
            {
                LlmConsts.ROLE: LlmConsts.ASSISTANT,
                LlmConsts.CONTENT: prompt_to_user
            }
        ]

    # Display chat messages
    display_chat_messages(st.session_state.messages)

    # 1. ユーザーからの質問を受け付ける。
    if query := st.chat_input():
        handle_user_query(query)


def show_search_ui():
    """
    検索用の UI を表示する。
    """

    setup_page(st, StConsts.PAGE_TITLE_SEARCH)

    st.session_state[StConsts.SESSION_KEY_RERANK_MODE] = create_rerank_mode_radio(st)

    st.text_input(label=StConsts.QUERY, key=StConsts.SESSION_KEY_QUERY)
    st.button(label=StConsts.SEARCH, on_click=search_onclick)


def show_ui(mode:UiMode, prompt_to_user:str = ''):
    """
    UI を表示する。モードに応じて RAG または検索画面を表示する。
    """
  
    if UiMode.is_rag(mode):
        show_rag_ui(prompt_to_user)
    else:
        show_search_ui()


def parse_ui_mode(args: list[str]) -> UiMode:
    """
    Parses the UI mode from command-line arguments.
    """
    mode_str = args[1] if len(args) > 1 else UiMode.SEARCH
    logger.debug(f"UI mode: {mode_str}")
    return UiMode.parse_mode(mode_str)


def get_or_initialize_es_client(my_env: dict[str, str]) -> Elasticsearch:
    """
    Retrieves or initializes the Elasticsearch client.
    """
    if StConsts.SESSION_KEY_ES_CLIENT in st.session_state:
        # return st.session_state.get(StConsts.SESSION_KEY_ES_CLIENT)
        return get_session_state_value(StConsts.SESSION_KEY_ES_CLIENT)

    es_client = initialize_es(
        my_env[EnvConsts.ELASTICSEARCH_ENDPOINT],
        my_env[EnvConsts.READ_API_KEY_ENCODED]
    )
    if es_client is None:
        raise ValueError("Failed to initialize Elasticsearch client.")

    st.session_state[StConsts.SESSION_KEY_ES_CLIENT] = es_client
    logger.debug(f"Elasticsearch client initialized: {es_client.info()}")
    return es_client


def initialize_llm_if_needed(ui_mode: UiMode, my_env: dict[str, str]) -> None:
    """
    Initializes the LLM instance if the mode is RAG.
    """
    if UiMode.is_rag(ui_mode) and StConsts.SESSION_KEY_LLM_INSTANCE not in st.session_state:
        llm_instance = initialize_llm_instance(my_env)
        if llm_instance is None:
            raise ValueError("Failed to initialize LLM instance.")

        st.session_state[StConsts.SESSION_KEY_LLM_INSTANCE] = llm_instance
        logger.debug(f"LLM instance initialized: {llm_instance}")


def main():
    try:
        my_env : dict[str, str] = load_env_wrapper()

        logger.debug(f'{my_env=}')

        ui_mode = parse_ui_mode(sys.argv)

        logger.debug(f'{ui_mode=}')

        es_client: Elasticsearch = get_or_initialize_es_client(my_env)
        initialize_llm_if_needed(ui_mode, my_env)
    except ValueError as e:
        print(f"Application failed.: {e}")
        logger.error(f"Application failed.: {e}")
        st.error("An unexpected error occurred. Please check the logs.")
        sys.exit(1)

    if es_client is None:
        print("Failed to create es_client")
        sys.exit(1)

    show_ui(ui_mode)


# --- main ---
if __name__ == '__main__':
    main()
