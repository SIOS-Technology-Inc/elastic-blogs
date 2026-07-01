"""インデックスを自動作成する。

このファイルの役割:
- 検索の入れ物（インデックス）と、その中のアナライザー設定を、Python から作る。
- es_scripts/01, 02 と同じ内容を、手作業（Kibana の Dev Tools）なしで再現できる。

比較を始める前に、まずこのファイルを1回実行してインデックスを用意する。

Kuromoji は必須。Sudachi はプラグイン未導入なら自動でスキップします。
"""

import os
import sys

# sys.path はモジュールを探す場所のリスト。
# このファイルがあるフォルダを先頭に足すことで、
# 同じフォルダの tokenize_es.py を import できるようにする。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tokenize_es import es_client

# 作成するインデックスの名前（後で何度も使うので変数にしておく）。
KUROMOJI_INDEX = "jp_kuromoji"
SUDACHI_INDEX = "jp_sudachi"

# Kuromoji 用のアナライザー設定。
# settings = インデックスの「設定」。ここでアナライザーの作り方を定義する。
# kuromoji_search は「mode: search の tokenizer」を使う自作アナライザー。
KUROMOJI_SETTINGS = {
    "analysis": {
        "tokenizer": {
            # mode: search は複合語を細かく分ける tokenizer の設定。
            # 例: 関西国際空港 → 関西 / 関西国際空港 / 国際 / 空港。
            "kuromoji_search_tok": {"type": "kuromoji_tokenizer", "mode": "search"}
        },
        "analyzer": {
            "kuromoji_search": {
                "type": "custom",
                "tokenizer": "kuromoji_search_tok",
                # filter = tokenizer の後にかける後処理の並び。
                # 標準の kuromoji アナライザーと同じ構成にそろえている。
                "filter": [
                    "kuromoji_baseform",        # 動詞などを基本形にそろえる
                    "kuromoji_part_of_speech",  # 不要な品詞を落とす
                    "ja_stop",                  # 日本語のストップワードを除く
                    "kuromoji_stemmer",         # 長音の処理など
                    "lowercase",                # 英字を小文字にそろえる
                ],
            }
        },
    }
}

# mappings = フィールド（列）の定義。どのフィールドにどのアナライザーを使うか。
KUROMOJI_MAPPINGS = {
    "properties": {
        # content は標準の kuromoji アナライザーを使うフィールド。
        "content": {"type": "text", "analyzer": "kuromoji"},
        # content_search は上で作った kuromoji_search を使うフィールド。
        "content_search": {"type": "text", "analyzer": "kuromoji_search"},
    }
}


def _sudachi_tokenizer(mode):
    """Sudachi の tokenizer 設定を作る小さなヘルパー。

    mode は分割の粒度: "A"（細かい）/ "B"（中間）/ "C"（大きい単位でまとめる）。
    関数にまとめることで、A/B/C を毎回書かずに済む。
    """
    return {"type": "sudachi_tokenizer", "split_mode": mode, "discard_punctuation": True}


def _sudachi_analyzer(tok):
    """指定した Sudachi tokenizer を使うアナライザー設定を作るヘルパー。"""
    return {
        "type": "custom",
        "tokenizer": tok,
        # Kuromoji と同じ思想で、基本形化・品詞フィルタ・ストップワード除去を行う。
        "filter": ["sudachi_baseform", "sudachi_part_of_speech", "sudachi_ja_stop"],
    }


# A/B/C の3つの tokenizer と、それぞれを使う3つのアナライザーをまとめて定義。
SUDACHI_SETTINGS = {
    "analysis": {
        "tokenizer": {
            "sudachi_a_tok": _sudachi_tokenizer("A"),
            "sudachi_b_tok": _sudachi_tokenizer("B"),
            "sudachi_c_tok": _sudachi_tokenizer("C"),
        },
        "analyzer": {
            "sudachi_a": _sudachi_analyzer("sudachi_a_tok"),
            "sudachi_b": _sudachi_analyzer("sudachi_b_tok"),
            "sudachi_c": _sudachi_analyzer("sudachi_c_tok"),
        },
    }
}

# A/B/C それぞれ専用のフィールドを用意する。
SUDACHI_MAPPINGS = {
    "properties": {
        "content_a": {"type": "text", "analyzer": "sudachi_a"},
        "content_b": {"type": "text", "analyzer": "sudachi_b"},
        "content_c": {"type": "text", "analyzer": "sudachi_c"},
    }
}


def recreate(es, name, settings, mappings):
    """インデックスを作り直す（あれば削除してから新規作成する）。

    delete の ignore_unavailable=True は「無くてもエラーにしない」指定。
    これで「初回でも2回目でも同じように動く」ようにしている。
    """
    es.indices.delete(index=name, ignore_unavailable=True)
    es.indices.create(index=name, settings=settings, mappings=mappings)
    print(f"[ok] created index: {name}")


def main():
    """このファイルを実行したときに動く本体。"""
    es = es_client()

    # Kuromoji は公式プラグイン。必須。
    recreate(es, KUROMOJI_INDEX, KUROMOJI_SETTINGS, KUROMOJI_MAPPINGS)

    # Sudachi は外部プラグイン。未導入なら作成に失敗するのでスキップする。
    # try で囲うことで、Sudachi が無くても Kuromoji の分は無駄にならない。
    try:
        recreate(es, SUDACHI_INDEX, SUDACHI_SETTINGS, SUDACHI_MAPPINGS)
    except Exception as e:
        print(f"[skip] Sudachi index は作成できませんでした: {e}")
        print("       Sudachi プラグインと辞書が入っているか確認してください。")


# このファイルを「直接」実行したときだけ main() を動かすおまじない。
# （他のファイルから import されたときは動かさない、という意味）
if __name__ == "__main__":
    main()
