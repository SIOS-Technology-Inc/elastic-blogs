"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

class KakinosukeConsts:
    """
    「柿之助」に関する定数.
    """

    # 検索対象のインデックス（のエイリアス）
    SEARCH_INDEX : str = 'kakinosuke'

    # 検索テンプレートのId
    SEARCH_TEMPLATE_ID_WITH_RERANK : str = 'rrf_search_template_with_rerank'
    SEARCH_TEMPLATE_ID_WITHOUT_RERANK : str = 'rrf_search_template_without_rerank'

    # フィールド名
    CHUNK_NO : str = 'chunk_no'
    CONTENT : str = 'content'

    # 「柿之助」検索用の定数
    QUERY_STRING : str = 'query_string'
    QUERY_FOR_VECTOR : str = 'query_for_vector'
    HIGHLIGHT : str = 'highlight'
