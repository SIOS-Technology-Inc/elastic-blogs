"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

import sys

from elasticsearch import Elasticsearch

from common.app_consts import AppConsts
from common.env_consts import EnvConsts

from common.load_env_wrapper import load_env_wrapper
from common.setup_logger import setup_logger

from elastic.es_func import initialize_es, bulk_from_file

"""
bulk を使ってテキストデータをインデックスに登録。

Usage:
    python src/bulk_main.py input_json_file

Example:
    python src/bulk_main.py data/kakinosuke.txt.json
"""

logger = setup_logger(__name__)


# --- main ---
if __name__ == '__main__':
    my_env : dict[str, str] = load_env_wrapper()

    logger.debug(f'{my_env=}')

    args: list[str] = sys.argv

    logger.debug(f'{len(args)=}')

    if len(args) < 2:
        print('argument is lack.')
        sys.exit(1)

    es_client: Elasticsearch = initialize_es(my_env[EnvConsts.ELASTICSEARCH_ENDPOINT], my_env[EnvConsts.WRITE_API_KEY_ENCODED])
  
    if es_client is None:
        print('es_client is null.')
        sys.exit(1)

    logger.debug(f"{es_client.info()}")

    bulk_from_file(es_client=es_client, input_text_filename=args[1], refresh=True)
