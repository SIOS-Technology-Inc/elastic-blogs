"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

# Elasticsearch に関する定数
class EsConsts:
    # 検索対象のインデックス
    SEARCH_INDEX = 'dls_sample_202507'

    # ドキュメントの本文を格納しているフィールド名
    CONTENT_FIELD_NAME = 'content'

    # 検索時に最大何件のドキュメントを返却するか?
    MAX_DOCS_COUNT = 10
