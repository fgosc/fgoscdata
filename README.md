# fgoscdata更新

※下記を実行しなくても動作します

# 新イベント(新章)追加フロー

## 1. アイテムデータの更新

### 1-1. get_data.py の実行
```
$ python get_data.py
```
- shortname.csvに未取得アイテムが記述される
- ce_gacha.txtに新規追加ガチャ産概念礼装が記述される

### 1-2.shortname.csv の編集
phash に存在しない(新)アイテム(name, shortname)の追記　

* ドロップするイベント限定概念礼装のshortnameを「礼装」「EXP礼装」等にする
* EXP礼装が複数レアリティででるイベントでは「★3EXP礼装」「★4EXP礼装］に変える
* ドロップ礼装が**一つのクエストで**同じレアリティで複数落ちるイベントで、礼装の名前が長い場合は短縮名を工夫してつける
* アイテム名が複数の単語を合成して構成されている場合、画像を見てわかるほうの一般名のほうを残してつける
  * ただし、「ポイント」はなるべく「ポイント」とつける

### 1-3. item_bl.txt の編集(滅多に無い)
 入ってはいけないアイテムをブラックリストファイルの編集で除外 

shortname.csv のデータからイベント交換アイテム以外の全てを抽出して登録(属性ではじかれているものもある)、shortname.csv からは消す

※ shortname.csvに間違ってデータが残っていても悪さをするといったことはない

### 1-4. ce_bl.txt の編集(滅多に無い)
イベント限定概念礼装で報酬で5枚のみ提供され、クエストでドロップしないものを追加

## 2. アイテム・概念礼装データの仮登録
### 2-1. hash_drop.json の作成

まずはfgosccalc用のアイテム・概念礼装とfgosccnt用の概念礼装データを登録する
```
$ python update.py
```

## 3. アイテムデータの本登録
### 3-1. hash_drop.json の再作成
fgosccnt でアイテムデータを認識できるようにする

1. アイテムデータの入った**バトルリザルトの**スクショを用意してfgosccnt.py で処理
2. 作成された新アイテムの item???.png, ce???.png, point???.png を正式名称にリネーム
(この時点でDropPriorityの認識などそのまま使用しても問題無く動作はする)
3. ハッシュ値回収プログラムの実行
```
$ python make_hash_battle.py
```

その後以下を実行する

```
$ python update.py
```
## 4. クエストデータの登録: (イベント名).json の作成
1. questIdを #fgo-updates の投稿などから取得する

例:

![image](https://user-images.githubusercontent.com/62515228/107876427-494b6a00-6f09-11eb-8903-4f3cab09f939.png)

この場合は 94056207 が questId となる

2. 概念礼装と種火以外埋まった戦利品表のスクショを入手して[questId].(jpg|png)と名前をつけ、img2str.pyで処理させる
```
$ python img2str.py [questId].jpg --csv
```
上記の例では
```
$ python img2str.py 94056207.jpg --csv
94056207,ゴッド・ラブ・ハント パッションラブ級,パッションラブ級,未ドロップ,卵,勲章,剣秘,剣魔,狂魔,剣モ,所持数無しアイテム,アロー,フェザー,,,,,,
```

3. 出力されたものをdata/csv/(イベント名).csv に追記して、自動生成が反映できない部分を修正する
- 概念礼装の正式名称(「未ドロップ」となっている)
- ポイント名称(「所持数無しアイテム」となってる)

例:
```
94056207,ゴッド・ラブ・ハント パッションラブ級,パッションラブ級,未ドロップ,卵,勲章,剣秘,剣魔,狂魔,剣モ,所持数無しアイテム,アロー,フェザー,,,,,,
↓
94056207,ゴッド・ラブ・ハント パッションラブ級,パッションラブ級,ホワイト・ガーデン,卵,勲章,剣秘,剣魔,狂魔,剣モ,ラブポイント,アロー,フェザー,,,,,,
```

4.  (イベント名).csv を変換して(イベント名).jsonを作成
```
$ python make_event_quest.py data/csv/(イベント名).csv
```

5. 反映させる

例:
```
git commit -a -m "event data upadte"
git push origin [branch]
cd ../fgosccalc/
git submodule update --remote
git commit -a -m "event data upadte"
git push origin [branch]
cd ../fgosccnt/
git submodule update --remote
git commit -a -m "event data upadte"
git push origin [branch]

```
