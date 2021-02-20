# streamlit を利用して Blender の context.copy() の結果を比較する
結果だけ見たい人は
```
streamlit run https://gist.githubusercontent.com/nikogoli/0819ef7c026a6f50786518822549f25f/raw/2bf882128815bb2878ae43f701ae0e3d767713ee/contexts_table.py
```

================**WIP**===============

#### 注意
* __手作業が多い__
* streamlit が必要
* 付属の blend ファイルは、ワークスペース"Scripting"のエリア分割を派手に変更している<br>
	→ ワークスペース"Scripting"の内容を変更したくない場合は、自分で blend ファイルを用意することを推奨する
* Mac での動作確認はしていない
<br><br>

### 全体の流れ
1. Blender にアドオンをインストールする
1. 各エディターごとに `context.copy()`を json ファイルで保存する　(アドオンの機能1)
1. 保存した json ファイルを1つにまとめる　(アドオンの機能2)
1. dataframe に変換した json を streamlit を利用して表示し、他のファイルと比較する
<br><br>

### 具体的な作業の流れ
1. `show_contexts.py`があるところに移動し、以下を実行してブラウザで context の表を眺める
```
streamlit run show_contexts.py
```
1. 付属の blend ファイルか、適当な blend ファイルを開く
1. export_context_addont.py を読み込む (`C:\Users\〇〇\AppData\Roaming\Blender Foundation\Blender\2.91\scripts\addons`の方に入るはず)
1. プリファレンスのアドオンのタブを「テスト中」に切り替え、「Custom: Export Context.copy()」を有効化する
1. アドオンのパネルを開くと(パスの内容は違うが)以下の設定パネルが出るので、必要に応じてパスを変更する
	* 初期設定では、`カレントディレクトリ/temp`が個別の json の保存先、`カレントディレクトリ/outcome`が結合した json の保存先となっている(はず)
	![アドオンの画像](https://github.com/nikogoli/blender_compare_contexts/blob/9ff1c394a5c7ee3c3bf9cb0364d80fc288626528/info/pref.png)
1. エリア分割状態が保存されていれば、画面の左上のほうが以下のようになっているはず
	![ウィンドウの画像](https://github.com/nikogoli/blender_compare_contexts/blob/9ff1c394a5c7ee3c3bf9cb0364d80fc288626528/info/image.png)
1. 調べたい状況になるように、右側のエリアで Blender を操作する
1. 左に並んだ16個の「CTX」ボタンを1つずつ押して、個別の json ファイルを保存する
1. アドオンの設定パネルで 状況に応じた名前を設定し、「Combine Json File」を押して json ファイルを結合する
1. ブラウザを更新すると左側の表示候補に結合したファイルが追加される
