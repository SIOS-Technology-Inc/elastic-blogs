"""Python 側でトークン化する（MeCab / Janome / Lindera）。

このファイルの役割:
- Elasticsearch の中ではなく、Python のライブラリで文章を単語に区切る。
- これらは ES の公式プラグインではないため、「事前トークン化（前処理）」として扱う。

機能語の除去について:
- 各ツールが持つ品詞情報を使い、clean.FUNCTION_POS と同じ基準で機能語を捨てる。
- こうすると、ES 側と Python 側で「残す/捨てる」基準がそろい、比較が公平になる。

注意:
- 各ライブラリの API はバージョンによって変わることがある。
  動かないときは、インストールしたバージョンの使い方に合わせて調整すること。
"""

# clean.py で定義した「内容語かどうか判定する関数」を借りてくる。
from clean import is_content_pos


def tokenize_mecab(text: str):
    """fugashi（MeCab ラッパー）でトークン化し、内容語だけ返す。

    fugashi = MeCab を Python から使いやすくしたライブラリ。
    """
    # import を関数の中に書いているのは、
    # 「このライブラリが入っていないときでも、他のアナライザーは動かす」ため。
    import fugashi

    # Tagger = 文章を解析する本体。
    tagger = fugashi.Tagger()
    tokens = []  # 残した単語をためる空リスト。
    # tagger(text) で1単語ずつ取り出してループする。
    for word in tagger(text):
        pos_major = word.feature.pos1  # 品詞の大分類
        # 品詞が取れて、かつ内容語なら残す。
        if pos_major and is_content_pos(pos_major):
            # 基本形があれば基本形に寄せる（なければ表層形）。
            # 例: 「抑えます」→ 基本形「抑える」。表記ゆれをまとめられる。
            # getattr(対象, "名前", 既定値) は「その属性が無くてもエラーにしない」取り方。
            base = getattr(word.feature, "lemma", None) or word.surface
            tokens.append(base)  # リストの末尾に追加。
    return tokens


def tokenize_janome(text: str):
    """Janome でトークン化し、内容語だけ返す。

    Janome = 純 Python 製の形態素解析器（C 言語の MeCab 本体が不要で導入が簡単）。
    """
    from janome.tokenizer import Tokenizer

    tokenizer = Tokenizer()
    tokens = []
    for token in tokenizer.tokenize(text):
        # Janome の品詞は「名詞,一般,*,*」のようなカンマ区切りの文字列。
        # split(",")[0] で先頭（大分類）だけを取り出す。
        pos_major = token.part_of_speech.split(",")[0]
        if is_content_pos(pos_major):
            # base_form が "*"（不明）のときは、見た目の形（surface）を使う。
            base = token.base_form if token.base_form != "*" else token.surface
            tokens.append(base)
    return tokens


def tokenize_lindera(text: str):
    """Lindera（Rust 製・Python バインディング）でトークン化する。

    Lindera = Rust 言語で書かれた新しい形態素解析器。速さが特長。
    lindera-py の API はバージョン差が大きい。動かない場合は、
    インストール済みバージョンの README に合わせて調整すること。
    """
    from lindera import Segmenter, Tokenizer, load_dictionary

    # 使う辞書を読み込む（ここでは ipadic という定番辞書）。
    dictionary = load_dictionary("ipadic")
    # Segmenter = 区切り方の設定。"normal" は標準的な分割モード。
    segmenter = Segmenter("normal", dictionary)
    tokenizer = Tokenizer(segmenter)

    tokens = []
    for token in tokenizer.tokenize(text):
        # details には品詞などの情報が入る。無い場合は空リストにしておく。
        details = getattr(token, "details", None) or []
        pos_major = details[0] if details else ""
        # 品詞が取れないときも、安全側で「残す」扱いにする。
        if not pos_major or is_content_pos(pos_major):
            tokens.append(token.text)
    return tokens


def tokenize_all_python(text: str) -> dict:
    """Python 側の全アナライザーでトークン化する。失敗したものはスキップ。"""
    # 「名前 -> 実行する関数」の対応表。
    # Python では関数も値として辞書に入れられる。
    funcs = {
        "mecab": tokenize_mecab,
        "janome": tokenize_janome,
        "lindera": tokenize_lindera,
    }
    out = {}
    for name, fn in funcs.items():
        # fn(text) で、その名前に対応する関数を実際に呼び出す。
        # ライブラリ未導入などで失敗したら、その1つだけ飛ばして続行する。
        try:
            out[name] = fn(text)
        except Exception as e:
            print(f"[skip] python analyzer {name}: {e}")
    return out
