"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

from typing import Iterable

import json
import logging

from elasticsearch import Elasticsearch, helpers

from common.app_consts import AppConsts
from common.env_consts import EnvConsts

from elastic.es_consts import EsConsts
from elastic.kakinosuke_consts import KakinosukeConsts


logger = logging.getLogger(__name__)


def create_es_client(elasticsearch_endpoint:str, api_key_encoded:str, timeout:int=EsConsts.DEFAULT_TIMEOUT) -> Elasticsearch:
  """
  Elasticsearch のクライアントを生成する。

  initialize_es()から呼ばれる。

  Returns:
    生成した Elasticsearch のクライアント
  """
  es_client: Elasticsearch = None
  if elasticsearch_endpoint != '' and api_key_encoded != '':
    es_client = Elasticsearch(hosts=elasticsearch_endpoint, api_key=api_key_encoded, timeout=timeout)
  return es_client


def initialize_es(elasticsearch_endpoint:str, api_key_encoded:str) -> Elasticsearch:
  """
  Elasticsearch のクライアントを初期化する。

  Returns:
    生成した Elasticsearch のクライアント
  """

  if elasticsearch_endpoint != '' and api_key_encoded != '':
    es_client: Elasticsearch = create_es_client(elasticsearch_endpoint, api_key_encoded)
    return es_client
  else:
    logger.error('please set elasticsearch_endpoint and api_key_encoded in .env')
    return None


def data_generator(input_json_file, index_name: str = KakinosukeConsts.SEARCH_INDEX):
    # json として読み込む。
    json_contents = json.load(input_json_file)

    for content in json_contents:
        # 1行ずつ処理する。
        yield {
            '_index': index_name,
            '_source': content
        }


def streaming_bulk_wrapper(es_client: Elasticsearch, actions) -> int:
  """
  bulk を使って、データを投入する。
  """
  success_count: int = 0
  for response in helpers.streaming_bulk(client=es_client, actions=actions):
    if response[0]:
      success_count += 1

  return success_count


def refresh_index(es_client: Elasticsearch, index_name=KakinosukeConsts.SEARCH_INDEX) -> None:
  """
  bulk 後などに、refresh を呼び出す。
  """
  es_client.indices.refresh(index=index_name)


def bulk_from_file(es_client: Elasticsearch, input_text_filename:str, refresh:bool = False, index_name=KakinosukeConsts.SEARCH_INDEX):
    """
    1つのtextファイルを1行ずつ読み込んで、elasticsearch にドキュメント登録する。
    (streaming_bulk を使用する)
    
    example of streaming_bulk
    https://www.programcreek.com/python/example/104890/elasticsearch.helpers.streaming_bulk
    """

    with open(file=input_text_filename, buffering=-1, encoding=AppConsts.DEFAULT_ENCODING) as input_file:
        success_count = streaming_bulk_wrapper(es_client=es_client, actions=data_generator(input_file))
        print(f'{success_count=}')
        
        if refresh and success_count > 0:
            refresh_index(es_client, index_name=index_name)


def create_search_params(query:str, highlight:bool=False) -> dict:
    """
    検索テンプレートに渡すためのパラメータを生成する。

    Returns:
      生成した、検索パラメータ
    """
    search_params = {
        KakinosukeConsts.QUERY_STRING: query,
        KakinosukeConsts.QUERY_FOR_VECTOR: query,
        KakinosukeConsts.HIGHLIGHT: highlight
    }

    return search_params


def extract_search_results(search_results, has_highlight: bool, field_name: str,
                           max_count: int) -> list[str]:
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
    for doc in search_results[EsConsts.HITS][EsConsts.HITS][:max_count]:
        if has_highlight and EsConsts.HIGHLIGHT in doc:
            results.append(doc[EsConsts.HIGHLIGHT][field_name])
        else:
            results.append(doc[EsConsts.FIELDS][field_name])

    return results


def es_search_template(es_client:Elasticsearch, search_params:dict, search_template_id:str,
                      search_index:str=KakinosukeConsts.SEARCH_INDEX, 
                      field_name:str= KakinosukeConsts.CONTENT, max_count:int=5) -> list[str]:
    """
    検索テンプレートを使って検索を行う。

    Returns:
        検索結果(list)
    """


    try:
        search_results = es_client.search_template(index=search_index, id=search_template_id, params=search_params)
    except Exception as e:
        logger.error(f'Search template execution failed: {e}')
        return []

    return extract_search_results(search_results, has_highlight = EsConsts.HIGHLIGHT in search_params,
                                field_name = field_name, max_count = max_count)
