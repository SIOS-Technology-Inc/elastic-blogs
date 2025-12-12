"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

import enum

class UiMode(enum.Enum):
    """
    UI のモードを定義するクラス(Enum)。
    """
    RAG = 'rag'
    SEARCH = 'search'

    @classmethod
    def is_rag(cls, mode:'UiMode') -> bool:
        return mode == cls.RAG

    @classmethod
    def parse_mode(cls, mode_str:str) -> 'UiMode':
        if mode_str == cls.RAG.value:
            return cls.RAG
        else:
            return cls.SEARCH
