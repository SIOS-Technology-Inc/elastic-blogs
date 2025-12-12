"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

class StConsts:
    """
    Streamlit に関する定数.
    """

    # Streamlit の session に保存するためのキー名.
    SESSION_KEY_ES_CLIENT : str = 'es_client'
    SESSION_KEY_LLM_INSTANCE : str = 'llm_instance'
    SESSION_KEY_MESSAGES : str = 'messages'
    SESSION_KEY_QUERY : str = 'query'
    SESSION_KEY_RERANK_MODE : str = 'rerank'

    # Streamlit で画面に表示する文字列
    SEMANTIC_RERANK : str = 'セマンティックリランク'
    NOT_DO : str = 'しない'
    DO : str = 'する'

    QUERY : str = 'クエリ'

    SEARCH : str = '検索'

    PAGE_TITLE_RAG : str = '柿之助 RAG'
    PAGE_TITLE_SEARCH : str = '柿之助の検索'

    DEFAULT_PROMPT : str = '質問を入力してください。'
