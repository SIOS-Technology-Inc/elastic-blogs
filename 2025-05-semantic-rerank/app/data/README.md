# README.md

## kakinosuke.txt

ここにある kakinosuke.txt は、[青空文庫](https://www.aozora.gr.jp/)から取得した「桃太郎」を
[http://www.kepe.net/ruby/](http://www.kepe.net/ruby/) を使ってルビを削除し、さらに、以下の変換を行ったものです。

| 元の単語 | 改変後の単語 |
|---|---|
| 桃太郎 | 柿之助 |
| 桃 | 柿 |
| 犬 | 猫 |
| 猿 | ゴリラ |
| きじ | 鷹 |
| きびだんご | おむすび |
| 鬼が島 | 悪霊島 |
| 鬼 | 悪霊 |


## kakinosuke.txt.json

ここにある kakinosuke.txt.json は、上記の kakinosuke.txt ファイルをチャンク分割し、json フォーマットで保存したものです。

下記の処理でチャンク分割し、json フォーマットで保存しています。

```
python src/split_text_main.py data/kakinosuke.txt 200 40
```
