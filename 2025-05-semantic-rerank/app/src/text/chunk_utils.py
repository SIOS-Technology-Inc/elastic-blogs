"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

import re
import sys

from typing import Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter

from common.app_consts import AppConsts
from elastic.kakinosuke_consts import KakinosukeConsts

"""
テキストファイルを読み込んで、content を チャンク分割するための関数を集めたファイル
"""

#----- 定数定義 ----->>>
# chunk分割時のセパレーター
# 欠点
# 先頭に "。" や "、" が来る場合がある。
# -> 後処理で、前の行の末尾に付け直す。
separators = ["\n\n", "\n", "。", "、", "，"," ", ""]
#----- 定数定義 -----<<<


class JapaneseCharacterTextSplitter(RecursiveCharacterTextSplitter):
    """句読点も句切り文字に含めるようにするためのスプリッタ"""

    def __init__(self, **kwargs):
        super().__init__(separators=separators, **kwargs)


def split_chunks(texts: str, chunk_size:int =AppConsts.DEFAULT_CHUNK_SIZE, chunk_overlap: int = AppConsts.DEFAULT_OVERLAP_SIZE) -> list[str]:
    """
    適当なサイズとオーバーラップでチャンク分割する
    """
    text_splitter = JapaneseCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return text_splitter.split_text(texts)


def process1file(input_text_filename:str, output_json_filename:str, chunk_size:int, chunk_overlap:int):
    """
    1つのtextファイルに対して、解析、分割を行う。
    """
    all_contents :str = ""
    
    with open(input_text_filename, "r", -1, AppConsts.DEFAULT_ENCODING) as input_file:
        contents: str = input_file.readlines()

    for content in contents:
        # 全角空白またはタブは半角空白に置換する。
        content = re.sub("[　\t]", " ", content)

        # 行頭の空白は削除する。
        content = re.sub(r"^[\s]+", "", content)
        
        all_contents += content
    
    # \s*\n\s+\n のような箇所は、\n\nでまとめる。
    all_contents = re.sub(r"\s*\n\s+\n", "\n\n", all_contents)

    # chunk 分割
    chunks: list[str] = split_chunks(all_contents, chunk_size, chunk_overlap)
    
    prev_line: str = ""
      
    chunk_no: int = 0

    # 分割処理しながら、チャンクを書き出す。
    with open(output_json_filename, "w", -1, AppConsts.DEFAULT_ENCODING) as output_file:
        # header 部分の書き出し
        output_file.write("[\n")
                
        for i, chunk in enumerate(chunks):

            # chunk内の\nを\\nに置換する。
            chunk: str = chunk.replace("\n", "\\n")
            
            if i == 0:
                # 先頭行は、読み込むだけとする。
                prev_line = chunk
                continue

            # 行末にあるべき区切り文字が行頭にある場合、前の行へ移動させる。
            # 本来なら、なくなるまで繰り返すべきだが、面倒なので、2回でやめている。
                
            m = re.match(r"^([\s。、，,）]+).*", chunk)
                   
            if m:
                # 行の先頭に 。，,）が来ることがある。
                # 次の行の先頭が、。，,）だったら、前の行の末尾に移動させる。
                matched_str: str = m.group(1)
                
                prev_line += matched_str
                chunk = chunk[len(matched_str):]
                
                if chunk == "":
                    # 次の行が、。）などのみの場合は、skip
                    continue
                    
                if chunk[0:2] == "\\n":
                    prev_line += "\\n"
                    chunk = chunk[2:]

                    m = re.match(r"^([\s。、，,）]+).*", chunk)
                   
                    if m:
                        # 行の先頭に 。，,）が来ることがある。
                        # 次の行の先頭が、。，,）だったら、前の行の末尾に移動させる。
                        matched_str: str = m.group(1)
                        
                        prev_line += matched_str
                        chunk = chunk[len(matched_str):]

                if chunk == "":
                    # 次の行が、。）などのみの場合は、skip
                    continue

            # sub-header 部分の書き出し
            if chunk_no > 0:
                output_file.write(",\n")
            
            chunk_no = chunk_no + 1

            output_file.write("{")
            output_file.write(f"\"chunk_no\":{chunk_no}, \"content\":\"{prev_line}\"")
            # sub-footer 部分の書き出し
            output_file.write("}")

            prev_line = chunk

        # 最終行、および、footer 部分の書き出し
        if chunk_no > 0:
            output_file.write(",\n")

        chunk_no = chunk_no + 1

        output_file.write("{")
        output_file.write(f"\"{KakinosukeConsts.CHUNK_NO}\":{chunk_no}, \"{KakinosukeConsts.CONTENT}\":\"{prev_line}\"")
        # sub-footer 部分の書き出し
        output_file.write("}")
        output_file.write("\n]\n")
