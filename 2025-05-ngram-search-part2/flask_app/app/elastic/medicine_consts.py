"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

class MedicineConsts:
    """
    Medicine インデックス（エイリアス）用の定数
    """
    
    # 検索対象のインデックス（のエイリアス）
    SEARCH_INDEX: str = 'medicine'

    # 検索テンプレートのId
    SEARCH_TEMPLATE_ID: str = 'search_medicine_with_ngram_202505'

    # 検索用パラメーター名1
    SEARCH_MEDICINE_NAME1 : str = 'search_medicine_name1'

    # 検索用パラメーター名2
    SEARCH_MEDICINE_NAME2 : str = 'search_medicine_name2'

    # フィールド名
    FIELD_MEDICINE_CODE : str = 'medicine_code'
    FIELD_MEDICINE_NAME : str = 'medicine_name'

    # 検索時の返却ドキュメント数のデフォルト値
    DEFAULT_SIZE : int = 30
