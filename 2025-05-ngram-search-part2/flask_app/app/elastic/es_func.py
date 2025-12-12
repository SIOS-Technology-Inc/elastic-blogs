"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

import time

from elasticsearch import Elasticsearch

from app.common.setup_logger import setup_logger

from app.elastic.es_consts import EsConsts
from app.elastic.medicine_consts import MedicineConsts


logger = setup_logger(__name__)

def create_es_client(elasticsearch_endpoint:str, api_key_encoded:str) -> Elasticsearch:
  """
  This function creates an instance of the Elasticsearch client that will be used to connect to the desired Elasticsearch endpoint.

  Args:
    elasticsearch_endpoint (str): The URL of the Elasticsearch server to which connections should be made.
    api_key_encoded (str): An encoded API key for authentication with the service. If the value is empty, no credentials are passed in the connection and anonymous access is used.

  Returns:
    es_client (object): A client object that can be used to interact with the desired Elasticsearch endpoint.
  """
  es_client: Elasticsearch = None
  if elasticsearch_endpoint != '' and api_key_encoded != '':
    es_client = Elasticsearch(hosts=elasticsearch_endpoint, api_key=api_key_encoded)
    logger.info('***** es_client is created. *****')
    logger.debug(es_client.info())
  return es_client


def initialize_es(endpoint: str, api_key_encoded:str) -> Elasticsearch:
  """
  Elasticsearch のクライアントを生成する。

  Args:
    endpoint (str): Elasticsearch の EndPoint (URL)
    api_key_encoded (str): Elasticsearch の API Key の encoded された値

  Returns:
    Elasticsearch のクライアントのインスタンス
  """

  if endpoint != '' and api_key_encoded != '':
    es_client: Elasticsearch = create_es_client(endpoint, api_key_encoded)
    return es_client
  else:
    logger.error(f'please specify endpoint and api_key_encoded.')
    return None


def create_search_params(search_medicine_name1:str, search_medicine_name2:str, size:int=MedicineConsts.DEFAULT_SIZE) -> dict:
  """
  This function creates and returns an object that holds all of the parameters needed for searching by way of a template in Elasticsearch.

  Args:
    search_medicine_name1 (str): 検索したい医薬品名の一部(2文字以上)
    search_medicine_name2 (str): 検索したい医薬品名の一部(空文字または、2文字以上)
    size (int): 

  Returns:
    search_params (dict): An object containing all of the above parameters.
  """
  search_params = {
      EsConsts.SIZE: size,
      MedicineConsts.SEARCH_MEDICINE_NAME1: search_medicine_name1,
      MedicineConsts.SEARCH_MEDICINE_NAME2: search_medicine_name2
  }

  return search_params


def es_search_template(es_client:Elasticsearch, search_params:dict, search_index:str=MedicineConsts.SEARCH_INDEX,
                       search_template_id:str=MedicineConsts.SEARCH_TEMPLATE_ID,
                       field_names:list=[MedicineConsts.FIELD_MEDICINE_CODE, MedicineConsts.FIELD_MEDICINE_NAME], max_count:int=MedicineConsts.DEFAULT_SIZE) -> list:
  """
  This function takes in an Elasticsearch client instance and a search parameter object which is then used to perform a template-based search.

  Args:
    es_client (Elasticsearch): An instance of the Elasticsearch client that should be used for performing this search.
    search_params (dict): A dictionary containing all parameters needed for the search, such as the query string or vector queries. The specific format and fields required here are defined elsewhere in the application configuration settings.
    search_index (str): The name of an existing index in a particular cluster. If left empty or not passed, then defaults to the name of the search index set up earlier in the application configuration.
    search_template_id (str): A unique identifier for this template within this specific Elasticsearch cluster. This should be defined elsewhere in the application configuration settings.
    field_names (list): The name of the field that will be used as a query vector if the query parameter is left empty.
    max_count (int): An integer value specifying how many results to retrieve and return from the search operation.

  Returns:
    results (list): A list containing all of the information returned by Elasticsearch for performing this template-based search.
  """
  
  start_time : int = time.time()

  search_results = es_client.search_template(index=search_index, id=search_template_id,
                                             params=search_params)

  results: list = []

  for doc in search_results[EsConsts.HITS][EsConsts.HITS][:max_count]:
    one_record = {}
    for field_name in field_names:
      # 配列で返ってくるので、先頭のみを取得する。
      one_record[field_name] = doc[EsConsts.FIELDS][field_name][0]
    results.append(one_record)

  elaps : int = time.time() - start_time
  logger.info(f'es_search_template end. {elaps=}')

  return results
