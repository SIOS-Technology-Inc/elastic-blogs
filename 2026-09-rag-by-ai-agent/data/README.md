# README.md

このフォルダには、サンプルデータとなる「柿之助」に関するデータを配置しています。

## [kakinosuke.txt](./kakinosuke.txt)

kakinosuke.txt は、[青空文庫](https://www.aozora.gr.jp/)から取得した「桃太郎」を
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


## [kakinosuke_chunked.ndjson](./kakinosuke_chunked.ndjson)

kakinosuke_chunked.ndjson は、kakinosuke_chunked.txt を元に NDJSON 化したファイルです。

Elasticsearch の Integration / Upload File 機能により、kakinosuke_tmp インデックスへアップロードします。


## [kakinosuke_chunked.txt](./kakinosuke_chunked.txt)

kakinosuke_chunked.txt は、kakinosuke.txt を一定のルールでチャンキングした結果です。

