"""共通のクリーニング・比較ユーティリティ。

このファイルは「部品（関数）の置き場」です。
ほかのファイル（compare.py など）から import して使います。
ここ単体では何も動きません（main がないため）。

方針（METHODOLOGY.md 参照）:
- 入力は NFKC 正規化を「入口」で一度だけ行い、全アナライザーに同じ入力を渡す。
  ※NFKC 正規化 = 全角・半角や記号の表記ゆれを、統一した形にそろえる処理。
    例: 全角の「３００」→ 半角の「300」。
- 機能語の除去は品詞ベースで行う（手書きストップワードに頼らない）。
  ※機能語 = 「は」「の」などの、それ自体に意味の薄い語。検索キーワードには向かない。
"""

# unicodedata は Python に最初から入っている標準ライブラリ。
# 文字の正規化（NFKC など）を行うために使う。
import unicodedata

# 機能語とみなす品詞（大分類）。各ツールの品詞表記にそろえる。
# ここを変えると、全アナライザーのクリーニング基準が一括で変わる。
#
# {...} は「集合（set）」というデータの入れ物。
# ・中身に重複がない
# ・「ある品詞がこの中に入っているか？」を高速に判定できる
# のが特徴で、今回のような「除外リスト」にちょうど良い。
FUNCTION_POS = {
    "助詞",
    "助動詞",
    "記号",
    "補助記号",
    "接続詞",
    "接続助詞",
    "フィラー",
    "感動詞",
    "空白",
}


def normalize_text(text: str) -> str:
    """入口での NFKC 正規化。全アナライザーに同じ入力を渡すために使う。

    引数 text: 正規化したい文字列（: str は「文字列を受け取る」という目印）。
    戻り値: 正規化して、前後の空白を取り除いた文字列（-> str は「文字列を返す」目印）。
    """
    # normalize("NFKC", text) で表記ゆれをそろえ、
    # .strip() で文字列の前後にある空白・改行を取り除く。
    return unicodedata.normalize("NFKC", text).strip()


def is_content_pos(pos_major: str) -> bool:
    """内容語（残す）なら True、機能語（捨てる）なら False。

    pos_major: 品詞の大分類（例: 「名詞」「助詞」）。
    """
    # 「pos_major が FUNCTION_POS の中に無い」＝機能語ではない＝内容語、と判定する。
    # not in は「含まれていない」という意味。
    return pos_major not in FUNCTION_POS


def jaccard(a, b) -> float:
    """2つのトークン集合の Jaccard 係数。両方空なら 1.0 とする。

    Jaccard 係数 = 2つの集合の「似ている度合い」を 0〜1 で表す数値。
    計算式は「両方に共通する要素数 ÷ どちらかに含まれる要素数」。
    1.0 に近いほど似ている。
    """
    # 受け取ったリストを set（集合）に変換する。
    # こうすると重複が消え、共通部分や和集合の計算がしやすくなる。
    sa, sb = set(a), set(b)
    # 両方とも空っぽなら「完全に同じ（＝1.0）」として扱う（ゼロ割りを避ける意味もある）。
    if not sa and not sb:
        return 1.0
    # sa & sb = 共通部分（積集合）、sa | sb = どちらかに含まれる全体（和集合）。
    # len(...) はその要素数。割り算で 0〜1 の値になる。
    return len(sa & sb) / len(sa | sb)


def pairwise_jaccard(token_sets: dict) -> dict:
    """{name: [tokens]} を受け取り、全ペアの Jaccard を返す。

    token_sets: {"kuromoji": [...], "sudachi_a": [...], ...} のような辞書（dict）。
                辞書 = 「名前（キー）」と「値」をペアで持つ入れ物。
    戻り値: アナライザー同士の総当たり表（これも辞書の入れ子）。
    """
    # 辞書のキー（アナライザー名）だけをリストとして取り出す。
    names = list(token_sets.keys())
    matrix = {}  # 結果の表をためていく、空の辞書。
    # 全アナライザーを2重ループで総当たりし、各ペアの似ている度合いを計算する。
    for i, n1 in enumerate(names):
        matrix[n1] = {}  # n1 の行を、空の辞書として用意する。
        for n2 in names:
            # round(値, 3) で小数第3位までに丸めて、表を見やすくする。
            matrix[n1][n2] = round(jaccard(token_sets[n1], token_sets[n2]), 3)
    return matrix
