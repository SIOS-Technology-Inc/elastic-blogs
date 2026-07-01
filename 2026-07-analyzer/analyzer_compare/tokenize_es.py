"""Elasticsearch の _analyze API でトークン化する。

このファイルの役割:
- Elasticsearch（以下 ES）の中で動くアナライザーに文章を渡し、
  単語（トークン）に区切ってもらう。
- 対象は Kuromoji（標準・mode: search）と Sudachi（A/B/C）。

ポイント:
Kuromoji と Sudachi は、ES のアナライザー内部で機能語の除去まで行う。
そのため、ここで返るトークンはすでにクリーニング済みとして扱う。
（MeCab/Janome は Python 側で品詞フィルタをかけるが、ここでは ES に任せる）

事前に es_scripts/01, 02 でインデックスを作成しておくこと。
（インデックス = ES の中のデータ置き場。アナライザーの設定もここに付いている）
"""

# os は OS とやり取りするための標準ライブラリ。
# ここでは「環境変数（.env で設定した接続先など）」を読むために使う。
import os

# elasticsearch は ES に接続するための外部ライブラリ（requirements.txt でインストール）。
from elasticsearch import Elasticsearch

# 各アナライザーが、どのインデックスに定義されているか。
# 「アナライザー名 -> インデックス名」の対応表（辞書）。
ES_ANALYZERS = {
    "kuromoji": "jp_kuromoji",
    "kuromoji_search": "jp_kuromoji",
    "sudachi_a": "jp_sudachi",
    "sudachi_b": "jp_sudachi",
    "sudachi_c": "jp_sudachi",
}


def es_client() -> Elasticsearch:
    """ES に接続するための「クライアント（窓口オブジェクト）」を作って返す。"""
    # os.environ.get("名前", "既定値") は環境変数を読む書き方。
    # 設定が無ければ既定値（ローカルの localhost:9201）を使う。
    url = os.environ.get("ES_URL", "http://localhost:9201")
    user = os.environ.get("ES_USERNAME") or ""
    password = os.environ.get("ES_PASSWORD") or ""
    # セキュリティ無効の検証クラスタでは認証なしで接続する。
    # ユーザー名とパスワードが設定されている場合だけ Basic 認証を使う。
    if user and password:
        return Elasticsearch(url, basic_auth=(user, password))
    return Elasticsearch(url)


def analyze(es: Elasticsearch, index: str, analyzer: str, text: str):
    """_analyze の結果からトークン文字列のリストを返す。

    _analyze API = 「この文章を、このアナライザーで区切るとどうなる？」を試せる ES の機能。
    """
    # ES に「このインデックスの、このアナライザーで text を解析して」と依頼する。
    res = es.indices.analyze(index=index, analyzer=analyzer, text=text)
    # 返ってくる結果は {"tokens": [{"token": "単語", ...}, ...]} という形。
    # そこから "token"（単語の文字列）だけを取り出してリストにする。
    # res.get("tokens", []) は「tokens が無ければ空リストを使う」安全な取り方。
    return [t["token"] for t in res.get("tokens", [])]


def tokenize_all_es(text: str) -> dict:
    """ES 上の全アナライザーでトークン化し、{name: [tokens]} を返す。"""
    es = es_client()
    out = {}  # 結果をためる辞書。
    # ES_ANALYZERS の各ペア（名前とインデックス）を順番に処理する。
    for name, index in ES_ANALYZERS.items():
        # try / except = 「失敗するかもしれない処理」を安全に行う書き方。
        # try の中でエラーが出たら except に飛び、止まらずに次へ進める。
        try:
            out[name] = analyze(es, index, name, text)
        except Exception as e:  # 接続不可・インデックス未作成など
            # 失敗しても全体を止めず、メッセージを出してそのアナライザーは飛ばす。
            print(f"[skip] ES analyzer {name}: {e}")
    return out


def es_version_info() -> dict:
    """再現性のためのバージョン情報（ES 本体・プラグイン）。

    「来年もう一度比べられるように」、使ったバージョンを記録するための関数。
    """
    es = es_client()
    info = {}
    # ES 本体のバージョン番号を取得する（取れなければエラーを記録）。
    try:
        info["version"] = es.info().get("version", {}).get("number")
    except Exception as e:
        info["version_error"] = str(e)
    # 入っているプラグイン一覧（_cat/plugins 相当）を取得する。
    try:
        plugins = es.cat.plugins(format="json")
        # ES クライアントは独自の応答オブジェクトを返すことがある。
        # .body があれば中の生データを取り出し、無ければそのまま使う。
        plugins = getattr(plugins, "body", plugins)
        info["plugins"] = plugins
    except Exception as e:
        info["plugins_error"] = str(e)
    return info
