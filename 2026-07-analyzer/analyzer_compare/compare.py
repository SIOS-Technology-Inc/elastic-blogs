"""比較の本体。

このファイルが、比較全体の「司令塔」です。
他のファイル（tokenize_es / tokenize_python / tokenize_llm / clean）を呼び出して、
結果をまとめて results/ に書き出します。

手順:
1. テキストを読み込み、入口で NFKC 正規化する（全アナライザー共通の入力）。
2. ES アナライザー / Python アナライザー / LLM（参考枠）でトークン化する。
3. トークン数、形態素解析器どうしのペアワイズ Jaccard を計算する。
4. 結果と、再現性のためのバージョン情報を results/ に書き出す。

実行方法（analyzer_compare ディレクトリ内で）:
    python compare.py
"""

# hashlib: 入力テキストの「指紋（SHA256）」を作るため。後で「同じ入力か」を確認できる。
# json: 結果を .json ファイルとして保存するため。
# os / sys: ファイルの場所や設定を扱うため。
# unicodedata: 用語の一致判定の前処理に使う。
# date: 実行日を記録するため。
import hashlib
import json
import os
import sys
import unicodedata
from datetime import date

# 同じディレクトリのモジュールを import できるようにする。
# （setup_indices.py と同じおまじない）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 自作の各ファイルから、使う関数・データを借りてくる。
# 末尾の # noqa: E402 は「import を上に書け、という警告を無視してよい」という印
# （sys.path を足してから import する必要があるため、あえて下に書いている）。
from clean import normalize_text, pairwise_jaccard  # noqa: E402
from tokenize_es import tokenize_all_es, es_version_info, ES_ANALYZERS  # noqa: E402
from tokenize_python import tokenize_all_python  # noqa: E402
from tokenize_llm import tokenize_all_llm, PROMPT_TEMPLATE  # noqa: E402

# .env ファイル（接続先や APIキー）を環境変数として読み込む。
# python-dotenv が無くても落ちないよう try で囲っている。
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# フォルダの場所を計算する。
# __file__ = このファイルのパス。dirname を2回たどって、プロジェクトの根っこを得る。
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")      # 入力テキストの置き場
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")  # 結果の出力先

# 比較に使うテキスト。「結果に付ける名前」と「ファイル名」の対応表。
TEXTS = {
    "text1_loxonin": "text1_loxonin.txt",
    "text2_medical": "text2_medical.txt",
}

# 形態素解析器（LLM は別枠なので含めない）。
# ES のアナライザー名 + Python 側の3つ、をつないだリスト。
ANALYZER_NAMES = list(ES_ANALYZERS.keys()) + ["mecab", "janome", "lindera"]

# 「専門用語が1語のまま残るか」を確認したい語。テストテキストに合わせる。
TECHNICAL_TERMS = {
    "text1_loxonin": [
        "ロキソニン",
        "解熱鎮痛",
        "非ステロイド性抗炎症薬",
        "NSAIDs",
        "炎症",
        "発熱",
    ],
    "text2_medical": [
        "アセトアミノフェン",
        "中枢神経系",
        "解熱鎮痛薬",
        "非ステロイド性抗炎症薬",
        "NSAIDs",
        "インフルエンザ",
        "300mg",
        "肝機能障害",
        "アナフィラキシーショック",
        "スティーブンス・ジョンソン症候群",
    ],
}


def _norm_for_match(s: str) -> str:
    """用語の一致確認用。NFKC + casefold で大小・全半角の違いを吸収する。

    casefold = 大文字小文字を区別しないための強力な小文字化。
    例: "NSAIDs" と "nsaids" を同じものとして扱える。
    """
    return unicodedata.normalize("NFKC", s).casefold()


def read_text(filename: str) -> str:
    """data フォルダの中の指定ファイルを読み込み、中身の文字列を返す。"""
    # with open(...) as f は「使い終わったら自動でファイルを閉じる」安全な開き方。
    # encoding="utf-8" は日本語が文字化けしないための指定。
    with open(os.path.join(DATA_DIR, filename), encoding="utf-8") as f:
        return f.read().strip()


def lib_versions() -> dict:
    """使ったライブラリのバージョンを集める（再現性のため）。"""
    # importlib.metadata で「インストール済みパッケージの版」を調べられる。
    from importlib.metadata import version, PackageNotFoundError

    # 版を知りたいパッケージの一覧。
    pkgs = [
        "elasticsearch",
        "sudachipy",
        "sudachidict_core",
        "fugashi",
        "unidic-lite",
        "janome",
        "lindera-py",
        "openai",
        "anthropic",
    ]
    # まず Python 本体の版を入れておく。
    out = {"python": sys.version.split()[0]}
    for p in pkgs:
        # 入っていれば版を、入っていなければ None（無い）を記録する。
        try:
            out[p] = version(p)
        except PackageNotFoundError:
            out[p] = None
    return out


def run_one_text(raw_text: str) -> dict:
    """1つのテキストについて、全アナライザーの結果をまとめて作る。"""
    # まず入口で正規化（全アナライザーに同じ入力を渡すため）。
    norm = normalize_text(raw_text)
    tokens = {}  # {アナライザー名: [トークン...]} をためる辞書。
    # update は「別の辞書の中身を、この辞書に足し込む」操作。
    tokens.update(tokenize_all_es(norm))      # ES のアナライザー群
    tokens.update(tokenize_all_python(norm))  # Python のアナライザー群
    llm_tokens = tokenize_all_llm(norm)       # LLM（参考枠）は別に持つ

    # 形態素解析器だけで Jaccard 行列を作る（LLM は別枠）。
    # 辞書内包表記: tokens から「名前が ANALYZER_NAMES に含まれるもの」だけ抜き出す。
    analyzer_tokens = {k: v for k, v in tokens.items() if k in ANALYZER_NAMES}

    # トークン数を数える。counts は重複込み、counts_unique は重複を除いた数。
    counts = {k: len(v) for k, v in tokens.items()}
    counts_unique = {k: len(set(v)) for k, v in tokens.items()}

    # この1テキスト分の結果を、1つの辞書にまとめて返す。
    return {
        "normalized_text": norm,
        "analyzer_tokens": tokens,
        "llm_tokens": llm_tokens,
        "counts": counts,
        "counts_unique": counts_unique,
        "pairwise_jaccard": pairwise_jaccard(analyzer_tokens),
    }


def _jaccard_table(r) -> list:
    """Jaccard の総当たり表を、Markdown の表（文字列の行リスト）に整形する。"""
    matrix = r["pairwise_jaccard"]
    names = list(matrix.keys())
    if not names:
        return []  # データが無ければ空のリストを返す。
    lines = ["### アナライザー間のペアワイズ Jaccard（1.0 が完全一致）\n"]
    # 表のヘッダー行と、区切り線（|---|---| …）を作る。
    lines.append("| | " + " | ".join(names) + " |")
    lines.append("|---|" + "|".join(["---"] * len(names)) + "|")
    # 1行ずつ、各アナライザーとの数値を並べる。
    for n1 in names:
        # f"{値:.2f}" は「小数第2位まで」で表示する書き方。
        row = [f"{matrix[n1][n2]:.2f}" for n2 in names]
        lines.append(f"| {n1} | " + " | ".join(row) + " |")
    lines.append("")
    return lines


def _term_table(text_name, r) -> list:
    """専門用語が1語で残ったかの ○×表を、Markdown に整形する。"""
    terms = TECHNICAL_TERMS.get(text_name, [])
    analyzers = list(r["analyzer_tokens"].keys())
    if not terms or not analyzers:
        return []
    # 各アナライザーの、正規化済みトークン集合。
    # こうしておくと「用語がその中にあるか」を ○×で高速に判定できる。
    norm_sets = {
        a: {_norm_for_match(t) for t in toks}
        for a, toks in r["analyzer_tokens"].items()
    }
    lines = ["### 専門用語が1語のまま残ったか（○ = 1トークンとして存在）\n"]
    lines.append("| 用語 | " + " | ".join(analyzers) + " |")
    lines.append("|---|" + "|".join(["---"] * len(analyzers)) + "|")
    for term in terms:
        tn = _norm_for_match(term)  # 用語側も同じ基準で正規化。
        # 各アナライザーの集合に入っていれば ○、無ければ ×。
        cells = ["○" if tn in norm_sets[a] else "×" for a in analyzers]
        lines.append(f"| {term} | " + " | ".join(cells) + " |")
    lines.append("")
    return lines


def write_summary(results: dict, metadata: dict):
    """全テキストの結果を、人が読みやすい summary.md にまとめて書き出す。"""
    lines = []  # 出力する行を順番にためていくリスト。
    lines.append("# 比較結果サマリー\n")
    lines.append(f"実行日: {metadata['run_date']}\n")
    lines.append(
        "注意: 本記事は2025年版と同一条件の定点観測ではありません。"
        "数値をそのまま前年と比較しないでください。\n"
    )
    # テキストごとにセクションを作る。
    for text_name, r in results.items():
        lines.append(f"\n## {text_name}\n")

        # トークン数の表。
        lines.append("### トークン数（ユニーク）\n")
        lines.append("| アナライザー | 件数 |")
        lines.append("|---|---|")
        for name, c in r["counts_unique"].items():
            lines.append(f"| {name} | {c} |")
        lines.append("")

        # 専門用語表と Jaccard 表を、上で作ったヘルパーで追加する。
        # extend は「リストの中身を全部足す」操作（append は1個だけ）。
        lines.extend(_term_table(text_name, r))
        lines.extend(_jaccard_table(r))

        # LLM が抽出したキーワードがあれば載せる。
        if r["llm_tokens"]:
            lines.append("### LLM（参考枠）が抽出したキーワード\n")
            for name, toks in r["llm_tokens"].items():
                lines.append(f"- **{name}**: {' / '.join(toks)}")
            lines.append("")
    # ためた行を改行でつないで、1つのファイルに書き出す。
    with open(os.path.join(RESULTS_DIR, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    """このファイルを実行したときに動く本体。比較全体を進める。"""
    # 出力先フォルダを用意する（既にあっても exist_ok=True でエラーにしない）。
    os.makedirs(RESULTS_DIR, exist_ok=True)

    results = {}  # 全テキストの結果をためる。
    dataset_for_hash = ""  # 指紋計算用に、全テキストをつなげた文字列。
    for text_name, filename in TEXTS.items():
        raw = read_text(filename)
        dataset_for_hash += raw
        results[text_name] = run_one_text(raw)
        # テキストごとに、生の結果を JSON で保存する。
        # ensure_ascii=False で日本語をそのまま、indent=2 で読みやすく整形。
        with open(
            os.path.join(RESULTS_DIR, f"{text_name}_tokens.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(results[text_name], f, ensure_ascii=False, indent=2)

    # 再現性のためのメタ情報（いつ・何のバージョンで・どんな入力で実行したか）。
    metadata = {
        "run_date": str(date.today()),
        # 入力テキストの SHA256 指紋。文字が1つ変わると値が変わるので、
        # 「同じ入力で再実行したか」を後から確認できる。
        "dataset_sha256": hashlib.sha256(dataset_for_hash.encode("utf-8")).hexdigest(),
        "elasticsearch": es_version_info(),
        "libraries": lib_versions(),
        "llm": {
            "eis_inference_ids": os.environ.get("EIS_COMPLETION_INFERENCE_IDS"),
            "openai_model": os.environ.get("OPENAI_MODEL"),
            "anthropic_model": os.environ.get("ANTHROPIC_MODEL"),
            "temperature": os.environ.get("LLM_TEMPERATURE"),
            "prompt": PROMPT_TEMPLATE,
        },
    }
    with open(
        os.path.join(RESULTS_DIR, "run_metadata.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # 最後に、人が読みやすいサマリーを書き出す。
    write_summary(results, metadata)
    print("done. results/ に出力しました。")


# 直接実行したときだけ main() を動かす。
if __name__ == "__main__":
    main()
