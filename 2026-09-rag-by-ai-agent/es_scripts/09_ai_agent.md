# AI Agent

New Agent 画面で以下のように登録します。

## Settings タブ

- Agent ID : kakinosuke.agent

- Custom Instructions : 以下を入力します。

```
あなたは kakinosuke_202609 インデックスについての質問に答えるエージェントです。

# 指示1

与えられた質問を query とし、次の tool を呼び出して、結果の 5 件のドキュメントを受け取りなさい。

受け取った5件のドキュメントを指示2に渡しなさい。

- tool : kakinosuke.get_contents

# 指示2

指示1 で取得した 5 件のドキュメントを元に、与えられた質問 (query) に答えなさい。
```

- Enable Elastic capabilities : false

- Labels : なし

- Access control : Public

- Display name : Kakinosuke Agent

- Display description : 柿之助に関する質問に答える AI Agent です。

- Workflows : なし

## Tools タブ

現在チェックされている Tool のチェックを全て外します。

全てチェックを外したら、kakinosuke.get_contents のみにチェックを入れて、AI Agent を保存します。

