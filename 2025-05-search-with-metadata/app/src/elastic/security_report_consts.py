"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

class SecurityReportConsts:
    """
    SIOSの有価証券報告書検索に関する定数.
    """

    # 検索対象のインデックス
    SEARCH_INDEX : str = 'sios_securities_report'

    # 検索テンプレートのId
    SEARCH_TEMPLATE_ID : str = 'search_with_meta_template_202505'
    
    # 返却用のフィールド名
    CONTENT : str = 'content'

    # 有価証券報告書検索用の定数
    QUERY : str = 'query'
    FISCAL_YEAR : str = 'fiscal_year'
