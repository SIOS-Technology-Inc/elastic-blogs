"""LLM は「参考枠」として扱う（アナライザー比較とは別カテゴリ）。

このファイルの役割:
- LLM（大規模言語モデル）に文章を渡し、「検索キーワードになりそうな語」を抜き出させる。
- これは Kuromoji / Sudachi のような「索引用トークナイザー」とは目的が違う。
  だから横並びの優劣比較はしない（あくまで参考）。

ここで見るのは「専門語を意味のまとまりとして拾えるか」「検索補助に使えそうか」。

接続の考え方（重要）:
- 形態素解析（Kuromoji / Sudachi）は、ローカルの Docker クラスタ（ES_URL）で行う。
- EIS の LLM 呼び出しは、Cloud 接続済みのクラスタ（EIS_ES_URL）で行う。
  例: すでに Cloud Connect 済みの既存3ノードクラスタ。
  ※EIS = Elastic Inference Service。ES 経由で AI モデルを呼べる仕組み。
- EIS を使う場合、OpenAI / Anthropic の個人キーは不要。

注意:
- LLM の tokenizer そのものは決定的だが、ここで使う「キーワード抽出」は生成タスクであり、
  temperature やモデルのバージョンの影響を受ける（非決定的になりうる）。
  ※temperature = 出力のばらつき具合。0 に近いほど毎回同じような答えになる。
- そのため、モデル名・プロンプト・temperature を必ず記録する（compare.py が記録する）。
"""

# json: 文字列とデータ（辞書/リスト）を相互変換する標準ライブラリ。
# os: 環境変数（APIキーなど）を読むため。
# re: 正規表現（文字パターンの検索）を扱う標準ライブラリ。
import json
import os
import re

# 箇条書き（- * ・ • や「1.」など）の行から中身を取り出す正規表現。
# LLM が JSON ではなく箇条書きで返したときの「保険」として使う。
_BULLET_RE = re.compile(r"^\s*(?:[-*・•]|\d+[.)])\s+(.*)$")

# どの LLM にも同じ指示を渡す。検索キーワード（意味のまとまり）を JSON 配列で返させる。
# {text} の部分は、あとで .format(text=...) で実際の文章に差し替える。
PROMPT_TEMPLATE = (
    "あなたは日本語検索のための補助です。\n"
    "次の文章から、検索のキーワードになる意味のまとまり"
    "（名詞・専門用語・固有名詞・薬品名・略語・数値表現など）を抽出してください。\n"
    "助詞・助動詞・記号は含めないでください。\n"
    "出力は、重複のない JSON 配列（文字列のみ）だけにしてください。説明は不要です。\n\n"
    "文章:\n{text}"
)


def _parse_json_array(content: str):
    """LLM の出力からキーワードのリストを取り出す。

    LLM の答えは「ただの文字列」なので、そこから語のリストを取り出す必要がある。

    1. まず JSON 配列として解釈を試みる（プロンプトはこれを要求している）。
    2. 失敗したら、箇条書きの行から拾うフォールバックを使う。
       （LLM が JSON ではなく「- テスト」のような形で返すことがあるため）
    """
    # content が None でも落ちないように "" を補い、前後の空白を取る。
    content = (content or "").strip()

    # 1) JSON 配列を優先。
    # 文字列の中から最初の "[" と最後の "]" の位置を探す。
    start = content.find("[")
    end = content.rfind("]")
    if start != -1 and end != -1:
        # find は「見つからなければ -1」を返す。両方見つかったときだけ中を取り出す。
        try:
            # [ から ] までを切り出して JSON として読み込む。
            arr = json.loads(content[start : end + 1])
            if isinstance(arr, list):  # ちゃんとリストになっているか確認。
                # 各要素を文字列にして前後空白を取り、空文字は捨てる。
                items = [str(x).strip() for x in arr]
                items = [x for x in items if x]
                if items:
                    return items
        except Exception:
            # JSON として壊れていたら、何もせず下のフォールバックへ進む。
            pass

    # 2) フォールバック: 箇条書きの行だけを拾う。
    #    見出しや「（…）」の補足説明は箇条書きでないので自然に除外される。
    items = []
    for line in content.splitlines():  # 1行ずつ調べる。
        m = _BULLET_RE.match(line)  # 箇条書きの形に一致するか？
        if not m:
            continue  # 一致しなければ次の行へ。
        # 一致した行から中身を取り出し、前後の記号・句読点を削る。
        kw = m.group(1).strip().strip(" 　.。、,")
        if kw:
            items.append(kw)
    return items


# --- EIS（推奨）-------------------------------------------------------------
def _eis_client():
    """EIS の推論エンドポイントを持つ、Cloud 接続済みクラスタへ接続する。"""
    from elasticsearch import Elasticsearch

    url = os.environ.get("EIS_ES_URL")
    if not url:
        # 接続先が無ければ、分かりやすいエラーを出してここで止める。
        raise RuntimeError("EIS_ES_URL が未設定です")
    api_key = os.environ.get("EIS_API_KEY")
    # 証明書検証を行うか。"false" のときだけ無効化する（自己署名証明書の検証環境向け）。
    verify = os.environ.get("EIS_VERIFY_CERTS", "true").lower() != "false"

    # kwargs = 接続時に渡す設定をためる辞書。条件に応じて中身を足していく。
    kwargs = {"verify_certs": verify}
    if not verify:
        kwargs["ssl_show_warn"] = False  # 検証オフ時の警告を黙らせる。
    if api_key:
        kwargs["api_key"] = api_key
    # **kwargs は「辞書を、名前付き引数として展開して渡す」書き方。
    return Elasticsearch(url, **kwargs)


def tokenize_eis(inference_id: str, text: str):
    """EIS の completion エンドポイントを inference API で呼ぶ。

    inference_id: 使う推論エンドポイントの ID（どのモデルを使うかの指定）。
    """
    es = _eis_client()
    # 生成には時間がかかることがあるので、タイムアウトを長めにする（120秒）。
    res = es.options(request_timeout=120).inference.inference(
        inference_id=inference_id,
        # プロンプトの {text} を実際の文章に置き換えて渡す。
        input=PROMPT_TEMPLATE.format(text=text),
    )
    # ES クライアントは dict ではなく ObjectApiResponse を返す。
    # .body で生の dict を取り出す（無ければ res をそのまま使う）。
    body = getattr(res, "body", res)
    content = ""
    # 応答の中から、生成された本文（completion の result）を取り出す。
    if isinstance(body, dict) and body.get("completion"):
        content = body["completion"][0].get("result", "")
    else:
        content = str(body)
    # 取り出した本文を、キーワードのリストに変換して返す。
    return _parse_json_array(content)


# --- 直接 OpenAI / Anthropic（EIS を使うなら不要）--------------------------
def tokenize_openai(text: str):
    """OpenAI の API を直接呼ぶ場合（EIS を使うなら不要）。"""
    from openai import OpenAI

    # APIキーは環境変数から取る。os.environ["..."] は「無ければエラー」で取る書き方。
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    model = os.environ.get("OPENAI_MODEL", "gpt-5.5")
    # temperature は文字列で入るので float（小数）に変換する。
    temperature = float(os.environ.get("LLM_TEMPERATURE", "0"))
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(text=text)}],
    )
    return _parse_json_array(resp.choices[0].message.content)


def tokenize_claude(text: str):
    """Anthropic（Claude）の API を直接呼ぶ場合（EIS を使うなら不要）。"""
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    model = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
    temperature = float(os.environ.get("LLM_TEMPERATURE", "0"))
    msg = client.messages.create(
        model=model,
        max_tokens=1024,  # 生成する最大トークン数（長すぎる出力を防ぐ）。
        temperature=temperature,
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(text=text)}],
    )
    return _parse_json_array(msg.content[0].text)


def tokenize_all_llm(text: str) -> dict:
    """利用可能な LLM だけ実行する。EIS を優先し、キーがあれば直接呼びも追加。

    「設定があるものだけ動かす」作り。何も設定していなければ空の辞書が返る。
    """
    out = {}

    # EIS（カンマ区切りで複数の inference ID を指定できる）。
    eis_ids = os.environ.get("EIS_COMPLETION_INFERENCE_IDS", "")
    # "a, b, c" のような文字列を "," で分け、前後空白を取り、空を捨てて1つずつ処理。
    for inference_id in [s.strip() for s in eis_ids.split(",") if s.strip()]:
        name = f"eis:{inference_id}"  # 結果に付ける名前（どの EIS か分かるように）。
        try:
            out[name] = tokenize_eis(inference_id, text)
        except Exception as e:
            print(f"[skip] {name}: {e}")

    # 直接 OpenAI / Anthropic（キーがある場合だけ）。
    if os.environ.get("OPENAI_API_KEY"):
        try:
            out["openai"] = tokenize_openai(text)
        except Exception as e:
            print(f"[skip] openai: {e}")
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            out["claude"] = tokenize_claude(text)
        except Exception as e:
            print(f"[skip] claude: {e}")

    return out
