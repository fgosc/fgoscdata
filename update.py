#!/usr/bin/env python3
#
# fgosccalcのデータアップデート
# hash_drop.json を作成
#
# FGO game data API https://api.atlasacademy.io/docs を使用
# 新アイテムが実装されたときどれぐらいのスピードで追加されるかは不明です
#
import requests
from pathlib import Path
import codecs
import csv
import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm
import json

Image_dir = Path(__file__).resolve().parent / Path("data/item/")
Image_dir_ce = Path(__file__).resolve().parent / Path("data/ce/")
CE_blacklist_file = Path(__file__).resolve().parent / Path("ce_bl.txt")
CE_gacha_file = Path(__file__).resolve().parent / Path("ce_gacha.txt")
Item_blacklist_file = Path(__file__).resolve().parent / Path("item_bl.txt")
shortname_file = Path(__file__).resolve().parent / Path("shortname.csv")
hash_exp_file = Path(__file__).resolve().parent / Path("hash_exp.csv")
hash_battle_file = Path(__file__).resolve().parent / Path("hash_battle.csv")
hash_replace_file = Path(__file__).resolve().parent / Path("hash_replace.csv")
#item_priority_file = Path(__file__).resolve().parent / Path("item_priority.csv")
Misc_dir = Path(__file__).resolve().parent / Path("data/misc/")
CE_output_file = Path(__file__).resolve().parent / Path("hash_ce.csv")
name_alias_file = Path(__file__).resolve().parent / Path("name_alias.csv")

##Item_output_file = Path(__file__).resolve().parent / Path("hash_item.csv")
##Drop_output_file = Path(__file__).resolve().parent / Path("hash_drop.csv")
Drop_json_file = Path(__file__).resolve().parent / Path("hash_drop.json")
mstItem_url = "https://raw.githubusercontent.com/FZFalzar/FGOData/master/JP_tables/item/mstItem.json"
if not Image_dir.is_dir():
    Image_dir.mkdir(parents=True)
if not Image_dir_ce.is_dir():
    Image_dir_ce.mkdir(parents=True)
if not Misc_dir .is_dir():
    Misc_dir .mkdir(parents=True)

ID_QP = 1
ID_QUEST_REWARD = 5

url_ce = "https://api.atlasacademy.io/export/JP/nice_equip.json"
url_ce_na = "https://api.atlasacademy.io/export/NA/nice_equip.json"
url_item = "https://api.atlasacademy.io/export/JP/nice_item.json"
url_item_na = "https://api.atlasacademy.io/export/NA/nice_item.json"

bg_files = {"zero":"listframes0_bg.png",
           "bronze":"listframes1_bg.png",
           "silver":"listframes2_bg.png",
           "gold":"listframes3_bg.png",
           "questClearQPReward":"listframes4_bg.png"
           }

bg_rarity = {3:"silver",
             4:"gold",
             5:"gold"}

bg_url = "https://raw.githubusercontent.com/atlasacademy/aa-db/master/build/assets/list/"
star_url = "https://raw.githubusercontent.com/atlasacademy/aa-db/master/build/assets/"
bg_image = {}
for bg in bg_files.keys():
    filename = Misc_dir / bg_files[bg]
    if filename.is_file() == False:
        url_download = bg_url + bg_files[bg]
        response = requests.get(url_download)
        with open(filename, 'wb') as saveFile:
            saveFile.write(response.content)
    tmpimg = cv2.imread(str(filename))
    h, w = tmpimg.shape[:2]
    bg_image[bg] = tmpimg[5:h-5,5:w-5]

hasher = cv2.img_hash.PHash_create()

servant_class = {'saber':'剣',
                 'lancer':'槍',
                 'archer':'弓',
                 'rider':'騎',
                 'caster':'術',
                 'assassin':'殺',
                 'berserker':'狂',
                 'ruler':'裁',
                 'avenger':'讐',
                 'alterEgo':'分',
                 'moonCancer':'月',
                 'foreigner':'降'}

ticket_list = [
    "シルバーベル",
    "手稿（真）","手稿（偽）","真紅の花びら", "奇跡のくつした",
    "冥界の砂",
    "AUOくじ", "アミーゴタオル",
    "AUOくじ2019","聖夜の絆創膏",
    ]

shortname = {}
with open(shortname_file, encoding='UTF-8') as f:
    reader = csv.DictReader(f)
    tmp = [row for row in reader]
for n in tmp:
    if n["shortname"] != "":
        shortname[n["name"]] = n["shortname"]

name_alias = {}
with open(name_alias_file, encoding='UTF-8') as f:
    reader = csv.DictReader(f)
    tmp = [row for row in reader]
for n in tmp:
#    tmp_alias = [shortname[n["name"]]] if n["name"] in shortname.keys() else []
    tmp_alias = []
    for m in n.keys():
        if m.startswith("alias"):
            if n[m] != "": tmp_alias.append(n[m])
    if len(tmp_alias) > 0: name_alias[int(n["id"])] = tmp_alias

##item_priority = {}
##with open(item_priority_file, encoding='UTF-8') as f:
##    reader = csv.DictReader(f)
##    tmp = [row for row in reader]
##for n in tmp:
##    item_priority[int(n["id"])] = n["priority"]

class CvOverlayImage(object):
    """
    [summary]
      OpenCV形式の画像に指定画像を重ねる
    
    https://qiita.com/Kazuhito/items/ff4d24cd012e40653d0c
    """

    def __init__(self):
        pass

    @classmethod
    def overlay(
            cls,
            cv_background_image,
            cv_overlay_image,
            point,
    ):
        """
        [summary]
          OpenCV形式の画像に指定画像を重ねる
        Parameters
        ----------
        cv_background_image : [OpenCV Image]
        cv_overlay_image : [OpenCV Image]
        point : [(x, y)]
        Returns : [OpenCV Image]
        """
        overlay_height, overlay_width = cv_overlay_image.shape[:2]

        # OpenCV形式の画像をPIL形式に変換(α値含む)
        # 背景画像
        cv_rgb_bg_image = cv2.cvtColor(cv_background_image, cv2.COLOR_BGR2RGB)
        pil_rgb_bg_image = Image.fromarray(cv_rgb_bg_image)
        pil_rgba_bg_image = pil_rgb_bg_image.convert('RGBA')
        # オーバーレイ画像
        cv_rgb_ol_image = cv2.cvtColor(cv_overlay_image, cv2.COLOR_BGRA2RGBA)
        pil_rgb_ol_image = Image.fromarray(cv_rgb_ol_image)
        pil_rgba_ol_image = pil_rgb_ol_image.convert('RGBA')

        # composite()は同サイズ画像同士が必須のため、合成用画像を用意
        pil_rgba_bg_temp = Image.new('RGBA', pil_rgba_bg_image.size,
                                     (255, 255, 255, 0))
        # 座標を指定し重ね合わせる
        pil_rgba_bg_temp.paste(pil_rgba_ol_image, point, pil_rgba_ol_image)
        result_image = \
            Image.alpha_composite(pil_rgba_bg_image, pil_rgba_bg_temp)

        # OpenCV形式画像へ変換
        cv_bgr_result_image = cv2.cvtColor(
            np.asarray(result_image), cv2.COLOR_RGBA2BGRA)

        return cv_bgr_result_image
    
def compute_hash_inner(img_rgb):
    img = img_rgb[34:104,:]    

    return hasher.compute(img)

def compute_hash(img_rgb):
    """
    判別器
    この判別器は下部のドロップ数を除いた部分を比較するもの
    記述した比率はiPpd2018画像の実測値
    """
    height, width = img_rgb.shape[:2]
    img = img_rgb[int(11/180*height):int(148/180*height),
                    int(10/166*width):int(156/166*width)]

##    cv2.imshow("img", cv2.resize(img, dsize=None, fx=5., fy=5.))
##    cv2.waitKey(0)
##    cv2.destroyAllWindows()
##    cv2.imwrite("item.png", img_rgb)
    return hasher.compute(img)

def compute_battle_hash(img_rgb):
    """
    判別器
    この判別器は下部のドロップ数を除いた部分を比較するもの
    記述した比率はiPhone6S画像の実測値
    """
    height, width = img_rgb.shape[:2]
    img = img_rgb[int(17/135*height):int(77/135*height),
                    int(19/135*width):int(103/135*width)]
    return hasher.compute(img)

def compute_hash_ce(img_rgb):
    """
    判別器
    この判別器は下部のドロップ数を除いた部分を比較するもの
    記述した比率はiPpd2018画像の実測値
    """
    height, width = img_rgb.shape[:2]
    img = img_rgb[5:115,3:119]

##    cv2.imshow("img", cv2.resize(img, dsize=None, fx=2., fy=2.))
##    cv2.waitKey(0)
##    cv2.destroyAllWindows()
    return hasher.compute(img)

def compute_hash_ce_narrow(img_rgb):
    """
    CE Identifier for scrolled down screenshot
    """
    height, width = img_rgb.shape[:2]
    img = img_rgb[int(30/206*height):int(155/206*height),
                  int(5/188*width):int(183/188*width)]

##    cv2.imshow("img", cv2.resize(img, dsize=None, fx=2., fy=2.))
##    cv2.waitKey(0)
##    cv2.destroyAllWindows()
    return hasher.compute(img)

def compute_gem_hash(img_rgb):
    """
    スキル石クラス判別器
    中央のクラスマークぎりぎりのハッシュを取る
    記述した比率はiPhone6S画像の実測値
    """
    height, width = img_rgb.shape[:2]
##    img = img_rgb[int(41/135*height):int(84/135*height),
##                  int(44/124*width):int(79/124*width)]
##    img = img_rgb[int((145-16-30/145*height):int(84/145*height),
##                  int(44/132*width):int(79/132*width)]
    img = img_rgb[int((145-16-60)/2/145*height):int((145-16+60)/2/145*height),
                  int((132-52)/2/132*width):int((132+52)/2/132*width)]

##    cv2.imshow("img", cv2.resize(img, dsize=None, fx=4., fy=4.))
##    cv2.waitKey(0)
##    cv2.destroyAllWindows()

    return hasher.compute(img)

def search_item_file(url, savedir):
    """
    url に該当するファイルを返す
    すでに存在したらダウンロードせずそれを使う
    """
    url_download = url
    tmp = url_download.split('/')
    savefilename = tmp[-1]
    Image_file = savedir / Path(savefilename)
    if savedir.is_dir() == False:
        savedir.mkdir()
    if Image_file.is_file() == False:
        response = requests.get(url_download)
        with open(Image_file, 'wb') as saveFile:
            saveFile.write(response.content)
    return Image_file

def overray_item(name, background, foreground):
    """
    枠画像とアイテム画像を合成する
    """
    bg_height, bg_width = background.shape[:2]
    fg_height, fg_width = foreground.shape[:2]
    point = (int((bg_width-fg_width)/2), int((bg_height-14-fg_height)/2))
    # 合成
    image = CvOverlayImage.overlay(background,
                                   foreground,
                                   point)

    return image

def overray_battle_item(name, background, foreground):
    """
    枠画像とアイテム画像を合成するバトルリザルト用(テスト版)
    """
    bg_height, bg_width = background.shape[:2]
    # 縮小 80%
    resizeScale = 0.8
    foreground = cv2.resize(foreground, (0,0), fx=resizeScale, fy=resizeScale, interpolation=cv2.INTER_AREA)

    fg_height, fg_width = foreground.shape[:2]
    point = (int((bg_width-fg_width)/2), int((bg_height-14-fg_height)/2))
    # 合成
    image = CvOverlayImage.overlay(background,
                                   foreground,
                                   point)

##    cv2.imshow("img", cv2.resize(image, dsize=None, fx=4., fy=4.))
##    cv2.waitKey(0)
##    cv2.destroyAllWindows()

    return image

def overray_ce(background, foreground):
    bg_height, bg_width = background.shape[:2]
    fg_height, fg_width = foreground.shape[:2]

    point = (bg_width-fg_width-5, bg_height-fg_height-5)
    # 合成
    image = CvOverlayImage.overlay(background,
                                   foreground,
                                   point)
    # 縮小 128→124
    wscale = (1.0 * 128) / 124
    resizeScale = 1 / wscale

    image = cv2.resize(image, (0,0), fx=resizeScale, fy=resizeScale, interpolation=cv2.INTER_AREA)

    return image

def name2nickname(name, item_nickname):
    #名前変換
    for i in item_nickname:
        if i["name"] == name:
            if i["nickname"] != "":
                name = i["nickname"]
                break
    return name

def cut_img_edge(img, name):
    height, width = img.shape[:2]
    return img

def make_item_data():
    """
    アイテムデータを作成
    """
    r_get = requests.get(url_item)
    item_list = r_get.json()
    r_get2 = requests.get(mstItem_url)
    mstItem_list = r_get2.json()
    r_get3 = requests.get(url_item_na)
    item_list_na = r_get3.json()

    id2dropPriority ={ item["id"]:item["dropPriority"] for item in mstItem_list}
    id2name_eng ={ item["id"]:item["name"] for item in item_list_na}
    
    with open(Item_blacklist_file, encoding='UTF-8') as f:
        bl_item = [s.strip() for s in f.readlines()]

    with open(hash_battle_file, encoding='UTF-8') as f:
        reader = csv.DictReader(f)
        tmp = [row for row in reader]
        id2hash_battle = {int(item["id"]):item["phash_battle"] for item in tmp}

    with open(hash_replace_file, encoding='UTF-8') as f:
        reader = csv.DictReader(f)
        tmp = [row for row in reader]
        id2hash_replace = {int(item["id"]):item["phash_relace"] for item in tmp}

##    with open(Item_nickname_file, encoding='UTF-8') as f:
##        reader = csv.DictReader(f)
##        item_nickname = [row for row in reader]
    name_list = [] #重複チェック用
##    item_output =[]
    order_gold = ['幼角', '根', '逆鱗', '心臓', '爪', '脂', '涙石']
    order_silver = ['八連', '蛇玉', '羽根', 'ホム', '蹄鉄', '頁', '歯車', 'ランタン', '種']
    order_bronze = ['塵', '牙', '骨', '証']
    item_rward_qp =[]
    item_gold =[]
    item_silver =[]
    item_bronze =[]
    item_gold_old =[]
    item_silver_old =[]
    item_bronze_old =[]
    secret_gem =[]
    magic_gem =[]
    gem =[]
    monuments = []
    pieces = []
    item_point =[]
    item_gold_event =[]
    item_silver_event =[]
    item_bronze_event =[]
    item_qp =[]

    for item in tqdm(item_list):

        name = item["name"]
        if item["type"] not in ["qp", "questRewardQp", "skillLvUp", "tdLvUp", "eventItem", "eventPoint", "boostItem", "dice"]:
            continue
        # 除外アイテムは読み込まない
        if name in bl_item:
            continue
        
#        tmp = [name2nickname(name, item_nickname)] + [out]
        tmp = {}
        
        tmp["id"] = item["id"]
        if item["name"] not in name_list:
            if item["id"] == ID_QUEST_REWARD:
                tmp["type"] = "Quest Reward"
            elif item["type"] == "eventPoint" and item["name"] != "アルトリウム":
                tmp["type"] = "Point"
            else:
                tmp["type"] = "Item"

            if item["background"] == "gold":
                tmp["rarity"] = 3
            elif item["background"] == "silver":
                tmp["rarity"] = 2
            elif item["background"] == "bronze":
                tmp["rarity"] = 1
            
            if item["id"] in id2hash_replace.keys():
                tmp["phash"]  = id2hash_replace[item["id"]]
            else:
                Image_file = search_item_file(item["icon"], Image_dir /str(item["background"]))
                fg_image = cv2.imread(str(Image_file), cv2.IMREAD_UNCHANGED)
                fg_image = cut_img_edge(fg_image, name)
                image = overray_item(name, bg_image[item['background']], fg_image)
                hash = compute_hash(image)
                hash_hex = ""
                for h in hash[0]:
                    hash_hex = hash_hex + "{:02x}".format(h)
                tmp["phash"]  = hash_hex
##            image_s = overray_battle_item(name, bg_image[item['background']], fg_image)
##            hash = compute_battle_hash(image_s)
##            hash_hex = ""
##            for h in hash[0]:
##                hash_hex = hash_hex + "{:02x}".format(h)
##            tmp["phash_battle"]  = hash_hex

            if 6000 < item["id"] < 6210:
                hash_gem = compute_gem_hash(image)
                hash_gem_hex = ""
                for h in hash_gem[0]:
                    hash_gem_hex = hash_gem_hex + "{:02x}".format(h)
                tmp["phash_class"]  = hash_gem_hex

            tmp["name"] = name
            if item["id"] in id2name_eng.keys():
                tmp["name_eng"] = id2name_eng[item["id"]]
            if name in shortname.keys():
                tmp["shortname"] = shortname[name]
            if item["id"] in name_alias.keys():
                tmp["alias"] = name_alias[item["id"]]
##            if item["id"] in item_priority.keys():
##                tmp["priority"] = item_priority[item["id"]]
            tmp["dropPriority"] = id2dropPriority[item["id"]]

            if item["id"] in id2hash_battle.keys():
                phash_battle = id2hash_battle[item["id"]]
                if phash_battle != "":
                    tmp["phash_battle"] = phash_battle
##                for bo in battle_output:
##                if item["id"] == int(bo["id"]) and bo["phash_battle"] != "":
##                    tmp["phash_battle"] = bo["phash_battle"]
##                    break

            if item["id"] == ID_QUEST_REWARD:
                item_rward_qp.append(tmp)
            elif item["id"] == ID_QP:
                item_qp.append(tmp)
##            elif 6500 < item["id"] < 6999:
            elif 6500 < item["id"] < 6522:
                if item["background"] == "gold":                
                    item_gold_old.append(tmp)
                elif item["background"] == "silver":
                    item_silver_old.append(tmp)
                else:
                    item_bronze_old.append(tmp)
            elif 6521 < item["id"] < 6999:
                if item["background"] == "gold":                
                    item_gold.append(tmp)
                elif item["background"] == "silver":
                    item_silver.append(tmp)
                else:
                    item_bronze.append(tmp)
            elif 6200 < item["id"] < 6210:
                secret_gem.append(tmp)
            elif 6100 < item["id"] < 6110:
                magic_gem.append(tmp)
            elif 6000 < item["id"] < 6010:
                gem.append(tmp)
            elif 7100 < item["id"] < 7110:
                monuments.append(tmp)
            elif 7000 < item["id"] < 7010:
                pieces.append(tmp)
            elif item["type"] in ["eventPoint", "dice"] \
                 or item["name"] in ticket_list:
                item_point.append(tmp)
            else:
                if item["background"] == "gold":                
                    item_gold_event.append(tmp)
                elif item["background"] == "silver":
                    item_silver_event.append(tmp)
                else:
                    item_bronze_event.append(tmp)
            name_list.append(item["name"])

##    point = {"id":30000000, "name":"ポイント", "type":"Point"}
##    item_point.append(point)

    item_output = []
    reward_output = []
##    priority = 0
    for item in item_rward_qp:
##        item["priority"] = priority
        reward_output.append(item)
##    priority = 410001
    for i, item in enumerate(reversed(item_gold)):
##        item["priority"] = priority + (i * 10)
        item_output.append(item)
##    priority = 415001
    for i, item in enumerate(order_gold):
        for j in item_gold_old:
            if item == j['shortname']:
##                j["priority"] = priority + (i * 10)
                item_output.append(j)
                break
##    priority = 420001
    for i, item in enumerate(reversed(item_silver)):
##        item["priority"] = priority + (i * 10)
        item_output.append(item)
##    priority = 425001
    for i, item in enumerate(order_silver):
        for j in item_silver_old:
            if item == j['shortname']:
##                j["priority"] = priority + (i * 10)
                item_output.append(j)
                break
##    priority = 430001
    for i, item in enumerate(reversed(item_bronze)):
##        item["priority"] = priority + (i * 10)
        item_output.append(item)
##    priority = 435001
    for i, item in enumerate(order_bronze):
        for j in item_bronze_old:
            if item == j['shortname']:
##                j["priority"] = priority + (i * 10)
                item_output.append(j)
                break
##    priority = 440001
    for i, item in enumerate(secret_gem):
##        item["priority"] = priority + (i * 10)
        item_output.append(item)
##    priority = 450001
    for i, item in enumerate(magic_gem):
##        item["priority"] = priority + (i * 10)
        item_output.append(item)
##    priority = 460001
    for i, item in enumerate(gem):
##        item["priority"] = priority + (i * 10)
        item_output.append(item)
##    priority = 470001
    for i, item in enumerate(monuments):
##        item["priority"] = priority + (i * 10)
        item_output.append(item)
##    priority = 480001
    for i, item in enumerate(pieces):
##        item["priority"] = priority + (i * 10)
        item_output.append(item)
##    priority = 500001
    for i, item in enumerate(reversed(item_point)):
##        item["priority"] = priority + (i * 10)
        item_output.append(item)
##    priority = 600001
    for i, item in enumerate(item_gold_event):
##        item["priority"] = priority + (i * 10)
        item_output.append(item)
##    priority = 700001
    for i, item in enumerate(item_silver_event):
##        item["priority"] = priority + (i * 10)
        item_output.append(item)
##    priority = 800001
    for i, item in enumerate(item_bronze_event):
##        item["priority"] = priority + (i * 10)
        item_output.append(item)
##    priority = 9999999
    for i, item in enumerate(item_qp):
##        item["priority"] = priority + (i * 10)
        item_output.append(item)

    return reward_output, item_output

##    header = ["id", "priority", "type", "name", "shortname", "phash"]
##    with open(Item_output_file, 'w', encoding="UTF-8") as f:
##        writer = csv.DictWriter(f, header, lineterminator="\n")
##        writer.writeheader()
##        writer.writerows(item_output)
            
            
##    item_rward_qp =[]
##    item_gold =[]
##    item_silver =[]
##    item_bronze =[]
##    secret_gem =[]
##    magic_gem =[]
##    gem =[]
##    monuments = []
##    pieces = []
##    item_point =[]
##    item_gold_event =[]
##    item_silver_event =[]
##    item_bronze_event =[]
##    item_qp =[]

def make_star_data():
    for i in range(3):
        filename = Misc_dir / ("star"  + str(i + 3) + ".png")
        if filename.is_file() == False:
            url_download = star_url + filename.name
            response = requests.get(url_download)
            with open(filename, 'wb') as savefile:
                savefile.write(response.content)    

def make_ce_data():
    make_star_data()
    ce_output = {}
    for i in range(3):
        ce_output[i + 3] = []

    r_get = requests.get(url_ce)
    ce_list = r_get.json()
    r_get2 = requests.get(url_ce_na)
    ce_list_na = r_get2.json()
    id2name_eng ={ item["id"]:item["name"] for item in ce_list_na}

    with open(CE_blacklist_file, encoding='UTF-8') as f:
        bl_ces = [s.strip() for s in f.readlines()]
    with open(CE_gacha_file, encoding='UTF-8') as f:
        gacha_ces = [s.strip() for s in f.readlines()]
    for ce in tqdm(ce_list):
        if ce["rarity"] <= 2:
            continue
        name = ce["name"]
        if ce["atkMax"]-ce["atkBase"]+ce["hpMax"]-ce["hpBase"]==0 \
           and not ce["name"].startswith("概念礼装EXPカード："):
            continue
        # 除外礼装は読み込まない
        if name in bl_ces + gacha_ces:
            continue
        mylist = list(ce['extraAssets']['faces']['equip'].values())
        Image_file =  search_item_file(mylist[0], Image_dir_ce /str(ce["rarity"]))
        ce_image = cv2.imread(str(Image_file))
        # IMREAD_UNCHANGEDを指定しα込みで読み込む
        star_image = cv2.imread(str(Misc_dir / ("star" + str(ce["rarity"]) + ".png")), cv2.IMREAD_UNCHANGED)
        image = overray_ce(ce_image, star_image)
        hash = compute_hash_ce(image)
        out = ""
        for h in hash[0]:
            out = out + "{:02x}".format(h)
        hash_narrow = compute_hash_ce_narrow(image)
        out_narrow = ""
        for h in hash_narrow[0]:
            out_narrow = out_narrow + "{:02x}".format(h)
        tmp = {}
        tmp["id"] = ce["id"]
        tmp["type"] = "Craft Essence"
        tmp["rarity"] = ce["rarity"]
        tmp["name"] = name
        if ce["id"] in id2name_eng.keys():
            tmp["name_eng"] = id2name_eng[ce["id"]]
        if name in shortname.keys():
            tmp["shortname"] = shortname[name]
        tmp["phash"]  = out
        tmp["phash_narrow"]  = out_narrow
#        tmp = [ce["id"]] + ["Craft Essence"] + [name] + [shortname[name] if name in shortname.keys() else "" ] + [out]
        ce_output[ce['rarity']].append(tmp)

    new_ce_output = []
##    header = ["id", "priority", "type", "name", "shortname", "phash"]
##    with open(CE_output_file, 'w', encoding="UTF-8") as f:
##        writer = csv.DictWriter(f, header,lineterminator="\n")
##        writer.writeheader()
    for i in range(3):
##        priority = 10000 + 100000 * (i + 1)
        dropPriority = 9000 + (5 - i)
        for n in ce_output[5 - i]:
##            n["priority"] = priority
            n["dropPriority"] = dropPriority
            new_ce_output.append(n)
##            priority = priority + 10
    return new_ce_output

if __name__ == '__main__':
    ce_output = make_ce_data()
    reward_output, item_output = make_item_data()
    with open(hash_exp_file, encoding='UTF-8') as f:
        reader = csv.DictReader(f)
        exp_output = []
        for row in reader:
            row2 = row.copy()
            for key in row.keys():
                if row[key] == "":
                    del row2[key] 
            row2["id"] = int(row["id"])
##            row2["priority"] = int(row["priority"])
            row2["dropPriority"] = int(row["dropPriority"])
            row2["rarity"] = int(row["rarity"])
            exp_output.append(row2)

##    header = ["id", "priority", "type", "rarity", "name", "shortname",
##              "phash", "phash_sold",
##              "phash_battle",
##              "phash_class", "phash_class_sold",
##              "phash_rarity", "phash_rarity_sold",
##              ]
##    with open(Drop_output_file, 'w', encoding="UTF-8") as f:
##        writer = csv.DictWriter(f, header, lineterminator="\n")
##        writer.writeheader()
##        writer.writerows(reward_output)
##        writer.writerows(ce_output)
##        writer.writerows(item_output)
##        writer.writerows(exp_output)
    with open(Drop_json_file, 'w', encoding="UTF-8") as f:
        f.write(json.dumps(reward_output + ce_output + item_output + exp_output, ensure_ascii=False, indent=4))
##        f.write(json.dumps(ce_output, ensure_ascii=False, indent=4))
##        f.write(json.dumps(item_output, ensure_ascii=False, indent=4))
##        f.write(json.dumps(exp_output, ensure_ascii=False, indent=4))
