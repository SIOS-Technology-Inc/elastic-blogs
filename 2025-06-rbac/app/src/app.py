"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

from typing import Dict

import streamlit as st
import streamlit_authenticator as stauth

import yaml
from yaml.loader import SafeLoader

from common.setup_logger import setup_logger
from elastic.es_func import create_es_client, extract_search_results


config_yaml_path = "config.yaml"

config = None

logger = setup_logger(__name__)

def search_wrapper(index_name: str):
    st.write(f"Index Name: {index_name}")

    api_key = config["credentials"]["usernames"][st.session_state["name"]]["api_key"]

    es_client = None

    if "es_client" in st.session_state:
        es_client = st.session_state["es_client"]
        if es_client is not None:
            logger.debug("es_client exists already. Reusing it.")

    if es_client is None:
        elasticsearch_endpoint = config["elasticsearch"]["endpoint"]
        logger.debug(f"Elasticsearch Endpoint: {elasticsearch_endpoint}")
        es_client = create_es_client(elasticsearch_endpoint, api_key)
        st.session_state["es_client"] = es_client
        logger.debug(f"Elasticsearch client created successfully. {es_client}")

    if es_client:
        search_query : Dict = {
            "query" : {
                "match_all": {}
            }
        }

        try:
            search_results = es_client.search(index=index_name, body=search_query)
        except Exception as e:
            st.error(f"Error during search: {e}")
            return
        
        st.write("Search Results:")
        for doc in extract_search_results(search_results):
            st.write(doc)
            logger.debug(f"Document: {doc}")

    else:
        st.write("Failed to create Elasticsearch client.")


def search_sales():
    index_name = "sales_data"
    search_wrapper(index_name)


def search_hr():
    index_name = "hr_data"
    search_wrapper(index_name)


def logout_callback(info):
    logger.debug(f"Logout callback info: {info}")
    
    if "es_client" in st.session_state:
        es_client = st.session_state.get("es_client")

        if es_client is not None:
            logger.debug("Closing Elasticsearch client.")
            es_client.close()

    st.session_state["es_client"] = None


def show_login_form():
    authenticator.login()
    if st.session_state["authentication_status"]:
        ## ログイン成功
        with st.sidebar:
            st.markdown(f'## Welcome *{st.session_state["name"]}*')
            authenticator.logout('Logout', 'sidebar', callback=logout_callback)

            st.divider()

            st.button(label='search sales_data', on_click=search_sales)
            st.button(label='search hr_data', on_click=search_hr)

    elif st.session_state["authentication_status"] is False:
        ## ログイン失敗
        st.error('Username/password is incorrect')

    elif st.session_state["authentication_status"] is None:
        ## デフォルト
        st.warning('Please enter your username and password')


if __name__ == '__main__':
    ## config.yaml の読み込み
    with open(config_yaml_path) as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        credentials=config['credentials'],
        cookie_name=config['cookie']['name'],
        cookie_key=config['cookie']['key'],
        cookie_expiry_days=config['cookie']['expiry_days'],
    )

    show_login_form()
 