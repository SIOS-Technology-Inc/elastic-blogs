"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

from typing import Iterable

from elastic.es_consts import SEARCH_INDEX
from elasticsearch import Elasticsearch, helpers
from common.setup_logger import setup_logger

logger = setup_logger(__name__)

def create_es_client(elasticsearch_endpoint: str, api_key_encoded: str) -> Elasticsearch:
    """
    Elasticsearch へアクセスするための client を生成する。

    Parameters:
    elasticsearch_endpoint (str): Elasticsearch の endpoint (URL)。
    api_key_encoded (str): Elasticsearch にアクセスするための (encoded された) Key。

    Returns:
    生成された Elasticsearch の client。
    """
    try:
        if elasticsearch_endpoint and api_key_encoded:
            es_client = Elasticsearch(hosts=elasticsearch_endpoint, api_key=api_key_encoded)
            logger.info("Elasticsearch client created successfully.")
            return es_client
        else:
            logger.error("Elasticsearch endpoint or API key is missing.")
            return None
    except Exception as e:
        logger.error(f"Error creating Elasticsearch client: {e}")
        return None


def streaming_bulk_wrapper(es_client: Elasticsearch, actions: Iterable) -> int:
    """
    bulk を使って、データを投入する。
    (streaming_bulk を使用する)

    Parameters:
    es_client (Elasticsearch): Elasticsearch の client。
    actions (Iterable): Elasticsearch に登録するデータの Iterable。

    Returns:
    投入したドキュメント数。
    
    See:
    https://elasticsearch-py.readthedocs.io/en/latest/helpers.html
    """
    success_count: int = 0
    try:
        for success, _ in helpers.streaming_bulk(client=es_client, actions=actions):
            if success:
                success_count += 1
        logger.info(f"Successfully indexed {success_count} documents.")
    except Exception as e:
        logger.error(f"Error during bulk indexing: {e}")
    return success_count


def refresh_index(es_client: Elasticsearch, index_name: str = SEARCH_INDEX):
    """
    bulk 後などに、refresh を呼び出す。

    Parameters:
    es_client (Elasticsearch): Elasticsearch の client。
    index_name (str): Refresh 対象のインデックス名（デフォルトは es_consts.py で定義した SEARCH_INDEX）。
    """
    try:
        es_client.indices.refresh(index=index_name)
        logger.info(f"Index {index_name} refreshed successfully.")
    except Exception as e:
        logger.error(f"Error refreshing index {index_name}: {e}")
