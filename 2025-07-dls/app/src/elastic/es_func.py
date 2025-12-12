"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

import logging
from typing import List, Optional
from elasticsearch import Elasticsearch

from common.setup_logger import setup_logger
from elastic.es_consts import EsConsts

logger = setup_logger(__name__)


def create_es_client(elasticsearch_endpoint: str, encoded_api_key: str) -> Optional[Elasticsearch]:
    """
    Elasticsearch へアクセスするための client を生成する。

    Parameters:
        elasticsearch_endpoint (str): Elasticsearch のエンドポイント.
        encoded_api_key (str): API key のエンコード済み文字列.
    
    Returns:
        Elasticsearch: Elasticsearch client のインスタンス.
    """

    logger.debug(f'Creating Elasticsearch client with endpoint: {elasticsearch_endpoint}')

    if elasticsearch_endpoint and encoded_api_key:
        try:
            return Elasticsearch(hosts=elasticsearch_endpoint, api_key=encoded_api_key)
        except Exception as e:
            logger.error(f'Failed to create Elasticsearch client: {e}')
            return None
    else:
        logger.error('Elasticsearch endpoint or API key is missing.')
        return None


def extract_search_results(search_results, field_name: str = EsConsts.CONTENT_FIELD_NAME,
                           max_count: int = EsConsts.MAX_DOCS_COUNT) -> List[str]:
    """
    検索結果から、指定したフィールドの値を抽出する。

    Parameters:
        search_results 検索結果.
        field_name (str): 抽出対象のフィールド名.
        max_count (int): 最大何件の検索結果を返すか?

    Returns:
        results (list): 抽出した値を格納したリスト.
    """
    logger.debug('-----')
    logger.debug(f'{search_results=}')
    logger.debug('-----')

    results = []
    for doc in search_results['hits']['hits'][:max_count]:
        results.append(doc['fields'][field_name])

    return results
