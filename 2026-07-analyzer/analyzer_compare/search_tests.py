"""実際の検索クエリで「期待する文書が拾えるか」を確認する。

このファイルの役割:
- トークンが似ているかどうかではなく、「検索として役に立つか」を見る。
- 少数の文書を ES に登録し、クエリごとに「ヒットしてほしい文書」を事前に決めて、
  本当にヒットするかを ○× で確認する。

なぜこれが大事か:
トークンがきれいに1語で残っても、検索で見つからなければ意味がない。
最後に効くのは「ユーザーが探したい文書が見つかるか」だから。

事前に setup_indices.py でインデックスを作成しておくこと。
結果は results/search_results.md と results/search_results.json に出力する。
"""

import json
import os
import sys
import unicodedata

# 同じフォルダの tokenize_es を import できるようにする（おまじない）。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tokenize_es import es_client

# .env を読み込む（接続先など）。無くても動くよう try で囲う。
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

# 検索アナライザー -> (インデックス, フィールド)
# 「どのアナライザーで検索するか」を、インデックスとフィールドの組で表す。
SEARCH_FIELDS = {
    "kuromoji": ("jp_kuromoji", "content"),
    "kuromoji_search": ("jp_kuromoji", "content_search"),
    "sudachi_a": ("jp_sudachi", "content_a"),
    "sudachi_b": ("jp_sudachi", "content_b"),
    "sudachi_c": ("jp_sudachi", "content_c"),
}

# 登録する文書。入口で NFKC 正規化して登録する。
# 各文書は {"id": 番号, "text": 本文} の辞書。
DOCS = [
    {"id": "1", "text": "関西国際空港は大阪府にある国際空港です。"},
    {
        "id": "2",
        "text": (
            "アセトアミノフェンは解熱鎮痛薬で、"
            "非ステロイド性抗炎症薬（NSAIDs）とは異なります。"
            "通常は1回300〜500mgを服用します。"
        ),
    },
    {"id": "3", "text": "ロキソニンは解熱鎮痛作用のある薬で、痛みや発熱を抑えます。"},
]

# クエリと、期待するヒット文書 ID。
# 「このクエリで検索したら、この ID の文書が出てきてほしい」という正解表。
QUERIES = [
    {"q": "空港", "expect": "1"},
    {"q": "関西空港", "expect": "1"},
    {"q": "NSAIDs", "expect": "2"},
    {"q": "300mg", "expect": "2"},
    {"q": "アセトアミノフェン", "expect": "2"},
]


def _nfkc(s: str) -> str:
    """文字列を NFKC 正規化する短いヘルパー。"""
    return unicodedata.normalize("NFKC", s)


def index_docs(es):
    """jp_kuromoji と jp_sudachi に同じ文書を登録する（正規化済み）。

    同じ本文を、Kuromoji 用と Sudachi 用の両方のインデックスに入れる。
    こうすると、まったく同じ文書で各アナライザーの検索を比べられる。
    """
    for doc in DOCS:
        text = _nfkc(doc["text"])  # 登録前に正規化。
        # Kuromoji 用インデックス（content と content_search の両方に入れる）。
        es.index(
            index="jp_kuromoji",
            id=doc["id"],
            document={"content": text, "content_search": text},
        )
        # Sudachi 用インデックス（プラグイン未導入で無ければ無視する）。
        try:
            es.index(
                index="jp_sudachi",
                id=doc["id"],
                document={"content_a": text, "content_b": text, "content_c": text},
            )
        except Exception:
            pass
    # refresh = 登録した文書をすぐ検索できる状態にする（反映を待たせる）。
    es.indices.refresh(index="jp_kuromoji")
    try:
        es.indices.refresh(index="jp_sudachi")
    except Exception:
        pass


def hits_for(es, index, field, query_text):
    """match クエリを実行し、ヒットした文書 ID のリストを返す。

    match クエリ = 指定フィールドに対する、ごく標準的な全文検索。
    """
    res = es.search(index=index, query={"match": {field: _nfkc(query_text)}}, size=10)
    # 検索結果の中から、ヒットした各文書の _id（ID）だけ取り出す。
    return [h["_id"] for h in res["hits"]["hits"]]


def main():
    """このファイルを実行したときに動く本体。"""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    es = es_client()
    index_docs(es)  # まず文書を登録する。

    # 使えるアナライザー（インデックスが存在するもの）だけ対象にする。
    # Sudachi が無い環境では Kuromoji だけになる。
    available = {}
    for name, (index, field) in SEARCH_FIELDS.items():
        if es.indices.exists(index=index):
            available[name] = (index, field)

    table = {}  # query -> {analyzer: {"hit": bool, "ids": [...]}}
    for item in QUERIES:
        q, expect = item["q"], item["expect"]
        # このクエリの結果をためる箱を用意する。
        table[q] = {"expect": expect, "results": {}}
        for name, (index, field) in available.items():
            try:
                ids = hits_for(es, index, field, q)
            except Exception as e:
                # 検索に失敗したら、エラー内容を記録して次へ。
                table[q]["results"][name] = {"error": str(e)}
                continue
            # expect（期待 ID）がヒット一覧に入っていれば hit=True。
            table[q]["results"][name] = {"hit": expect in ids, "ids": ids}

    # JSON 出力（生の結果。後で細かく確認できる）。
    with open(
        os.path.join(RESULTS_DIR, "search_results.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(table, f, ensure_ascii=False, indent=2)

    # Markdown 出力（人が読みやすい ○× の表）。
    names = list(available.keys())
    lines = ["# 検索クエリでの動作確認\n"]
    lines.append("○ = 期待する文書がヒット、× = ヒットせず。\n")
    lines.append("| クエリ | 期待文書 | " + " | ".join(names) + " |")
    lines.append("|---|---|" + "|".join(["---"] * len(names)) + "|")
    for q, info in table.items():
        cells = []
        for name in names:
            r = info["results"].get(name, {})
            if "error" in r:
                cells.append("?")  # エラーだったところは ? にする。
            else:
                cells.append("○" if r.get("hit") else "×")
        lines.append(f"| {q} | doc {info['expect']} | " + " | ".join(cells) + " |")
    with open(
        os.path.join(RESULTS_DIR, "search_results.md"), "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(lines))

    print("done. results/search_results.md を確認してください。")


# 直接実行したときだけ main() を動かす。
if __name__ == "__main__":
    main()
