"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

class EsConsts:
    # 検索対象のインデックス（のエイリアス）
    SEARCH_INDEX: str = 'medicine'

    # 検索テンプレートのId
    SEARCH_TEMPLATE_ID: str = 'search_medicine_with_ngram_202505'

    # Elasticsearch 内の一般的な定数
    HITS : str = 'hits'
    FIELDS : str = 'fields'
    SIZE : str = 'size'
