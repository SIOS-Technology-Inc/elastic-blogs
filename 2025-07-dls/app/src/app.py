"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

from typing import Any, Dict

import streamlit as st
import streamlit_authenticator as stauth

import yaml
from yaml.loader import SafeLoader

from common.session_consts import SessionConsts
from common.setup_logger import setup_logger
from elastic.es_consts import EsConsts
from elastic.es_func import create_es_client, extract_search_results


config_yaml_path = "config.yaml"

config = None

logger = setup_logger(__name__)


def search() -> None:
    """
    Elasticsearch へ接続して、検索を行う。
    """

    index_name = EsConsts.SEARCH_INDEX

    login_name = st.session_state.get(SessionConsts.NAME)

    if login_name is None:
        st.error("User is not logged in.")
        return

    encoded_api_key = config["credentials"]["usernames"][login_name]["encoded_api_key"]

    es_client = st.session_state.get(SessionConsts.ES_CLIENT)

    if es_client is not None:
        logger.debug("es_client exists already. Reusing it.")
    else:
        elasticsearch_endpoint = config["elasticsearch"]["endpoint"]
        logger.debug(f"Elasticsearch Endpoint: {elasticsearch_endpoint}")
        es_client = create_es_client(elasticsearch_endpoint, encoded_api_key)
        if es_client is not None:
            try:
                logger.debug(es_client.info())
                st.session_state[SessionConsts.ES_CLIENT] = es_client
                logger.debug(f"Elasticsearch client created successfully. {es_client}")
            except Exception as e:
                logger.error(f"Failed to get Elasticsearch info: {e}")
                es_client = None

    if es_client:
        search_query : Dict[str, Any] = {
            "_source": False,
            "fields": [EsConsts.CONTENT_FIELD_NAME],
            "query" : {
                "match_all": {}
            }
        }

        try:
            search_results = es_client.search(index=index_name, body=search_query)
            outputs = []        
            for doc in extract_search_results(search_results):
                logger.debug(f"Document: {doc}")
                outputs.append(doc[0])
            st.write(outputs)
        except Exception as e:
            logger.error(f"Error during search: {e}")
            st.write("An error occurred during the search operation.")

    else:
        st.write("Failed to create Elasticsearch client.")


def logout_callback(info: Any) -> None:
    """
    ログアウト時のコールバック関数。
    """
    logger.debug(f"Logout callback info: {info}")
    
    es_client = st.session_state.get(SessionConsts.ES_CLIENT)

    if es_client is not None:
        logger.debug("Closing Elasticsearch client.")
        try:
            es_client.close()
        except Exception as e:
            logger.error(f"Failed to close Elasticsearch client: {e}")

    st.session_state.clear()


def show_login_form(authenticator: stauth.Authenticate) -> None:
    """
    ログインフォームを表示する。
    """
    logger.debug("Showing login form.")

    authenticator.login()

    auth_status = st.session_state.get(SessionConsts.AUTHENTICATION_STATUS)

    if auth_status:
        ## ログイン成功
        with st.sidebar:
            st.markdown(f'## Welcome *{st.session_state.get(SessionConsts.NAME)}*')
            authenticator.logout('Logout', 'sidebar', callback=logout_callback)

        if st.button(label="Search", key=SessionConsts.SEARCH):
            search()

    elif auth_status is False:
        ## ログイン失敗
        st.error('Username/password is incorrect')

    elif auth_status is None:
        ## デフォルト
        st.warning('Please enter your username and password')


if __name__ == '__main__':
    """
    Document Level Security の動作確認アプリケーション。
    """
    logger.debug("Starting the application.")
    
    # config.yaml の読み込み
    with open(config_yaml_path) as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        credentials=config['credentials'],
        cookie_name=config['cookie']['name'],
        cookie_key=config['cookie']['key'],
        cookie_expiry_days=config['cookie']['expiry_days'],
    )

    show_login_form(authenticator)
 