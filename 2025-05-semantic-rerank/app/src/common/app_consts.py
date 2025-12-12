"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

class AppConsts:
    """
    このアプリに関する定数.
    """

    # Bulk の前処理で読み込むテキストファイルのエンコーディング
    DEFAULT_ENCODING : str = 'utf-8'

    # Bulk の前処理での ChunkSize, OverlapSize のデフォルト値
    DEFAULT_CHUNK_SIZE : int = 200
    DEFAULT_OVERLAP_SIZE : int = 40

    MIN_CHUNK_SIZE : int = 100
