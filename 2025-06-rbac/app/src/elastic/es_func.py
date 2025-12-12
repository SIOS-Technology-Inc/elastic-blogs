"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

from typing import Dict, List, Optional
from elastic.es_consts import MAX_DOCS_COUNT
from elasticsearch import Elasticsearch

from common.setup_logger import setup_logger

logger = setup_logger(__name__)


def create_es_client(elasticsearch_endpoint: str, api_key_encoded: str) -> Optional[Elasticsearch]:
    """
    Elasticsearch へアクセスするための client を生成する。

    Parameters:
        elasticsearch_endpoint (str): Elasticsearch のエンドポイント.
        api_key_encoded (str): API key のエンコード済み文字列.
    
    Returns:
        Elasticsearch: Elasticsearch client のインスタンス.
    """
    if elasticsearch_endpoint and api_key_encoded:
        try:
            return Elasticsearch(hosts=elasticsearch_endpoint, api_key=api_key_encoded)
        except Exception as e:
            logger.error(f'Failed to create Elasticsearch client: {e}')
            return None
    else:
        logger.error('Elasticsearch endpoint or API key is missing.')
        return None


def extract_search_results(search_results,
                           max_count: int = MAX_DOCS_COUNT) -> List[str]:
    """
    検索結果から、指定したフィールドの値を抽出する。

    Parameters:
        search_results 検索結果.
        max_count (int): 最大何件の検索結果を返すか?

    Returns:
        results (List): 抽出した値を格納したリスト.
    """
    logger.debug('-----')
    logger.debug(f'{search_results=}')
    logger.debug('-----')

    results = []
    for doc in search_results['hits']['hits'][:max_count]:
        results.append(doc['_source'])

    return results
