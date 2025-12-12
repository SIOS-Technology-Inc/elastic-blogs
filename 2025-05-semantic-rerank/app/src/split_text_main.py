"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

import sys

from common.app_consts import AppConsts

from text.chunk_utils import process1file

"""
テキストデータをチャンク分割し、jsonファイルに保存する。

チャンク分割した json ファイルは、元のファイル名 + ".json" というファイル名で保存されます。

Usage:
    python src/split_text_main.py input_data_path [chunk_size] [overlap_size]

Example:
    python src/split_text_main.py data/kakinosuke.txt 200 40
"""


# ----- main -----
if __name__ == '__main__':
    args: list[str] = sys.argv

    text_filepath: str = args[1]

    chunk_size: int = AppConsts.DEFAULT_CHUNK_SIZE
    if len(args) > 2:
        chunk_size = int(args[2])
        if chunk_size < AppConsts.MIN_CHUNK_SIZE:
            chunk_size = AppConsts.MIN_CHUNK_SIZE

    overlap_size: int = AppConsts.DEFAULT_OVERLAP_SIZE
    if len(args) > 4:
        overlap_size = int(args[3])
        if overlap_size < 0:
            overlap_size = 0

    output_json_filepath: str = text_filepath + ".json"

    process1file(text_filepath, output_json_filepath, chunk_size, overlap_size)
