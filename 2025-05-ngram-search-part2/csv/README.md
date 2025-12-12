# README.md

## y_20250415.csv

y_20250415.csv ファイルは、下記からダウンロードした 2025年04月15日時点の医薬品マスターです。

https://shinryohoshu.mhlw.go.jp/shinryohoshu/downloadMenu/


## y_20250415_col2_utf8.csv

y_20250415_col2_utf8.csv ファイルは、下記のようにして作成します。

1. 上記の y_20250415.csv を LibreOffice や Excel で開く。
2. 3列目と5列目のみを残し、他の列を削除する。
3. 先頭に行を挿入する。
4. 先頭行の値に medicine_code, medicine_name をそれぞれ入力する。
5. y_20250415_col2.csv として保存する。
6. y_20250415_col2.csv をメモ帳などで開き、utf-8 で保存する。その際、ファイル名を y_20250415_col2_utf8.csv とする。
