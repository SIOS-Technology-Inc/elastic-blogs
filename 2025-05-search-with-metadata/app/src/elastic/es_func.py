"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

from typing import Iterable
import logging

from elasticsearch import Elasticsearch, helpers

from common.env_consts import EnvConsts
from elastic.es_consts import EsConsts
from elastic.security_report_consts import SecurityReportConsts


logger = logging.getLogger(__name__)


def create_es_client(elasticsearch_endpoint:str, api_key_encoded:str) -> Elasticsearch:
  """
  Elasticsearch のクライアントを生成する。

  initialize_es()から呼ばれる。

  Return:
    生成した Elasticsearch のクライアント
  """
  es_client: Elasticsearch = None
  if elasticsearch_endpoint != '' and api_key_encoded != '':
    es_client = Elasticsearch(hosts=elasticsearch_endpoint, api_key=api_key_encoded)
  return es_client


def initialize_es(my_env: dict) -> Elasticsearch:
  """
  Elasticsearch のクライアントを初期化する。

  Return:
    生成した Elasticsearch のクライアント
  """

  if EnvConsts.ELASTICSEARCH_ENDPOINT in my_env and EnvConsts.READ_API_KEY_ENCODED in my_env:
    es_client: Elasticsearch = create_es_client(my_env[EnvConsts.ELASTICSEARCH_ENDPOINT], my_env[EnvConsts.READ_API_KEY_ENCODED])
    return es_client
  else:
    logger = logging.getLogger(__name__)
    logger.error('please set elasticsearch_endpoint and read_api_key_encoded in .env')
    return None


def create_search_params(query:str, fiscal_year:str) -> dict:
  """
  検索テンプレートに渡すためのパラメータを生成する。

  Return:
    生成した、検索パラメータ
  """
  search_params = {
      SecurityReportConsts.QUERY: query,
      SecurityReportConsts.FISCAL_YEAR: fiscal_year
  }

  return search_params


def es_search_template(es_client:Elasticsearch, search_params:dict, search_index:str=SecurityReportConsts.SEARCH_INDEX,
                       search_template_id:str=SecurityReportConsts.SEARCH_TEMPLATE_ID,
                       field_name:str= SecurityReportConsts.CONTENT, max_count:int=5) -> list:
  """
  検索テンプレートを使って検索を行う。

  Return:
    検索結果(list)
  """

  search_results = es_client.search_template(index=search_index, id=search_template_id,
                                             params=search_params)

  # Debug messages for troubleshooting purposes
  logger.debug('-----')
  logger.debug(f'{search_results=}')
  logger.debug('-----')

  results: list = []

  for doc in search_results[EsConsts.HITS][EsConsts.HITS][:max_count]:
    # Debug message for troubleshooting purposes
    logger.debug(f'{doc=}')
    results.append(doc[EsConsts.FIELDS][field_name])

  return results
