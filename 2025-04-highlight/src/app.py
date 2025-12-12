"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License

検索画面を表示する。

Usage:
  streamlit run src/app.py
"""

from typing import Dict, Mapping
import sys

import streamlit as st
from elastic.es_func import initialize_es, create_search_params, es_search_template
from elasticsearch import Elasticsearch

from common.load_env_wrapper import load_env_wrapper
from common.setup_logger import setup_logger

# st.session_state に格納する際の Key
ES_CLIENT : str = 'es_client'
QUERY : str = 'query'
SHOW_HIGHLIGHT : str = 'show_highlight'

NO : str = 'いいえ'
YES : str = 'はい'


logger = setup_logger(__name__)


def search(es_client: Elasticsearch, query: str, show_highlight: str = '') -> list:
    """
    Elasticsearch に検索処理を依頼し、検索結果を受け取る。

    Parameters:
        es_client (Elasticsearch) : Elasticsearch client のインスタンス.
        query (str) : 検索クエリ.
        show_highlight (str) : ハイライト表示するかどうか? (する場合は'はい').
    
    Rerurns:
        list : 検索結果
    """
    show_highlight_bool = show_highlight == YES

    # 検索用パラメタを生成する。
    search_params: Mapping[str, any] = create_search_params(query, show_highlight_bool)

    try:
        # 検索テンプレートを使って検索する。
        search_results: list = es_search_template(es_client, search_params)
    except Exception as e:
        logger.error(f'Error during search: {e}')
        return []

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
    query = st.session_state[QUERY]
    st.write(f'検索クエリ: {query}')

    # 2. Elasticsearch へ問い合わせ / 3.検索結果の受け取り
    es_client = st.session_state[ES_CLIENT]
    show_highlight = st.session_state[SHOW_HIGHLIGHT]

    search_results = search(es_client, query, show_highlight)
  
    # 4. 検索結果の表示
    for i, results in enumerate(search_results):
        st.write(f'-- {i+1} --')
        for sub_result in results:
            st.write(f'{sub_result}', unsafe_allow_html=True)


def show_search_ui():
    """
    検索用の UI を表示する。
    """
    st.set_page_config(layout="wide", page_title='柿之助 検索アプリ')
    st.text_input(label='クエリ', key=QUERY)
    st.button(label='検索', on_click=search_onclick)

    show_highlight = st.sidebar.radio(
        label='ハイライト表示する',
        options=[NO, YES]
    )

    st.session_state[SHOW_HIGHLIGHT] = show_highlight
    logger.debug(f'show_highlight={st.session_state[SHOW_HIGHLIGHT]}')


# ----- main -----
if __name__ == '__main__':
    es_client: Elasticsearch

    if 'es_client' in st.session_state:
        es_client = st.session_state[ES_CLIENT]
    else:
        my_env: Dict[str, str] = load_env_wrapper()

        try:
            es_client = initialize_es(my_env)
        except Exception as e:
            logger.error(f'Failed to initialize Elasticsearch: {e}')
            sys.exit(1)

        st.session_state[ES_CLIENT] = es_client
        logger.info(f'{es_client.info()}')

    if es_client is None:
        logger.error('es_client is None.')
        sys.exit(1)

    show_search_ui()
