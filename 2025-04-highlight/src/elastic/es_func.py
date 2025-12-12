"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

import logging
from typing import Dict, Mapping, List, Optional
from elastic.es_consts import SEARCH_INDEX, SEARCH_TEMPLATE_ID, CONTENT_FIELD_NAME
from elasticsearch import Elasticsearch

from common.load_env_wrapper import ELASTICSEARCH_ENDPOINT, READ_API_KEY_ENCODED


FIELDS : str = 'fields'
HITS : str = 'hits'
HIGHLIGHT : str = 'highlight'

QUERY_STRING : str = 'query_string'
QUERY_FOR_VECTOR : str = 'query_for_vector'

# ハイブリッド検索時に最大何件のドキュメントを返却するか?
MAX_DOCS_COUNT = 5

logger = logging.getLogger(__name__)


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


def initialize_es(my_env: Dict[str, str]) -> Optional[Elasticsearch]:
    """
    Elasticsearch のクライアントを初期化する。

    Parameters:
        my_env (Dict): .env ファイルの内容を格納した辞書.
    
    Returns:
        Elasticsearch client のインスタンス (エラー時は None).
    """
    es_client = create_es_client(my_env.get(ELASTICSEARCH_ENDPOINT, ''), my_env.get(READ_API_KEY_ENCODED, ''))
    if es_client:
        return es_client
    else:
        logger.error(f'Please set {ELASTICSEARCH_ENDPOINT} and {READ_API_KEY_ENCODED} in .env')
        return None


def create_search_params(query: str, highlight: bool = False) -> Mapping[str, any]:
    """
    検索テンプレートに埋め込むパラメタを生成する。

    Parameters:
        query (str): 検索クエリ
        highlight (bool): ハイライト表示を行うかどうか?

    Returns:
        Mapping: 検索テンプレートに渡すパラメタ.
    """
    return {
        QUERY_STRING : query,
        QUERY_FOR_VECTOR : query,
        HIGHLIGHT : highlight
    }


def extract_search_results(search_results, has_highlight: bool = False, field_name: str = CONTENT_FIELD_NAME,
                           max_count: int = MAX_DOCS_COUNT) -> List[str]:
    """
    検索結果から、指定したフィールドの値を抽出する。

    Parameters:
        search_results 検索結果.
        has_highlight (bool): ハイライト表示を行うかどうか?
        field_name (str): 抽出対象のフィールド名.
        max_count (int): 最大何件の検索結果を返すか?

    Returns:
        results (list): 抽出した値を格納したリスト.
    """
    logger.debug('-----')
    logger.debug(f'{search_results=}')
    logger.debug('-----')

    results = []
    for doc in search_results[HITS][HITS][:max_count]:
        if has_highlight and HIGHLIGHT in doc:
            results.append(doc[HIGHLIGHT][field_name])
        else:
            results.append(doc[FIELDS][field_name])

    return results


def es_search_template(es_client: Elasticsearch, search_params: Mapping[str, any], search_index: str = SEARCH_INDEX,
                       search_template_id: str = SEARCH_TEMPLATE_ID, field_name: str = CONTENT_FIELD_NAME,
                       max_count: int = MAX_DOCS_COUNT) -> List[str]:
    """
    検索テンプレートを使って、検索を行う。

    Parameters:
        es_client (Elasticsearch): Elasticsearch client のインスタンス.
        search_params (Mapping): 検索パラメータ.
        search_index (str): 検索対象のインデックス名.
        search_template_id (str): 検索テンプレートId.
        field_name (str): 返却対象のフィールド名.
        max_count (int): 最大何件の検索結果を返すか?

    Returns:
        results (list): 検索結果を格納した list.
    """
    try:
        search_results = es_client.search_template(index=search_index, id=search_template_id, params=search_params)
    except Exception as e:
        logger.error(f'Search template execution failed: {e}')
        return []

    return extract_search_results(search_results, has_highlight = HIGHLIGHT in search_params,
                                  field_name = field_name, max_count = max_count)
