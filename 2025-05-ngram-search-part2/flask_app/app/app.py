"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

import sys

from flask import Flask, render_template, request

from elasticsearch import Elasticsearch

from app.common.env_consts import EnvConsts
from app.common.http_consts import HttpConsts
from app.common.load_env_wrapper import load_env_wrapper
from app.common.setup_logger import setup_logger
from app.elastic.medicine_consts import MedicineConsts
from app.elastic.es_func import initialize_es, create_search_params, es_search_template

app = Flask(__name__)

logger = setup_logger(__name__)

if __name__ == 'app.app':

    es_client: Elasticsearch = None

    my_env: dict[str, str] = load_env_wrapper()

    try:
        if EnvConsts.ELASTICSEARCH_ENDPOINT in my_env and EnvConsts.READ_API_KEY_ENCODED in my_env:
            es_client: Elasticsearch = initialize_es(my_env[EnvConsts.ELASTICSEARCH_ENDPOINT], my_env[EnvConsts.READ_API_KEY_ENCODED])
    except Exception as e:
        logger.error(f'Failed to initialize Elasticsearch: {e}')
        sys.exit(1)

    if es_client is None:
        logger.error('es_client is None.')
        sys.exit(1)


@app.route(f'/', methods=[HttpConsts.GET])
def index():
    return render_template("index.html")


@app.route('/search_medicine', methods=[HttpConsts.POST])
def search():
    """
    Ajax で呼び出される関数
    画面の部分書き換えを行う。
    
    returns:
        検索結果のリスト
    """

    json_data = request.json
    search_medicine_name1 = json_data[MedicineConsts.SEARCH_MEDICINE_NAME1]
    search_medicine_name2 = json_data[MedicineConsts.SEARCH_MEDICINE_NAME2]

    search_params = create_search_params(search_medicine_name1, search_medicine_name2, size=MedicineConsts.DEFAULT_SIZE)
    
    # Elasticsearch に検索を依頼する。
    search_results = es_search_template(es_client=es_client, search_params=search_params, max_count=MedicineConsts.DEFAULT_SIZE)

    return search_results
