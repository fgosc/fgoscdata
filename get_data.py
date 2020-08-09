#!/usr/bin/env python3
import argparse
import logging
import requests
import json
from pathlib import Path
import csv

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

kazemai_url = "https://fgo.square.ovh/kazemai/kazemai.json"
item_url = "https://api.atlasacademy.io/export/JP/nice_item.json"
ce_url = "https://api.atlasacademy.io/export/JP/nice_equip.json"
Item_blacklist_file = Path(__file__).resolve().parent / Path("item_bl.txt")
shortname_file = Path(__file__).resolve().parent / Path("shortname.csv")
filename = "kazemai.json"
CE_blacklist_file = Path(__file__).resolve().parent / Path("ce_bl.txt")
CE_gacha_file = Path(__file__).resolve().parent / Path("ce_gacha.txt")


def get_kazemai():
    # kazemai file の保存
    r_get = requests.get(kazemai_url)
    kazemai = r_get.json()

    with open(filename, mode="w", encoding="UTF-8") as f:
        f.write(json.dumps(kazemai, ensure_ascii=False, indent=2))


def main(args):
    get_kazemai()

    # phash に存在しない(新)アイテム(id, name)の追記(shortname.csv, name_alias.csv)
    r_get = requests.get(item_url)
    item_list = r_get.json()

    with open(shortname_file, encoding='UTF-8') as f:
        reader = csv.DictReader(f)
        shortnames = [row for row in reader]

    with open(Item_blacklist_file, encoding='UTF-8') as f:
        bl_item = [s.strip() for s in f.readlines()]

    name2shortname = {}
    for item in shortnames:
        name2shortname[item["name"]] = item["shortname"]

    for item in item_list:
        if item["type"] not in ["qp", "questRewardQp", "skillLvUp",
                                "tdLvUp", "eventItem", "eventPoint", "dice"]:
            continue
        if item["name"] not in bl_item:
            if item["name"] not in name2shortname.keys():
                name2shortname[item["name"]] = ""

    # 概念礼装
    r_get = requests.get(ce_url)

    ce_list = r_get.json()
    with open(CE_blacklist_file, encoding='UTF-8') as f:
        bl_ces = [s.strip() for s in f.readlines()]
    with open(CE_gacha_file, encoding='UTF-8') as f:
        gacha_ces = [s.strip() for s in f.readlines()]
    for ce in ce_list:
        if ce["rarity"] <= 2:
            continue
        name = ce["name"]
        if ce["atkMax"]-ce["atkBase"]+ce["hpMax"]-ce["hpBase"] == 0 \
           and not ce["name"].startswith("概念礼装EXPカード："):
            continue
        # 除外礼装は読み込まない
        if name in bl_ces + gacha_ces:
            continue
        if ce["name"] not in name2shortname.keys():
            name2shortname[ce["name"]] = ""

    rows = [[k, v] for k, v in name2shortname.items()]
    with open(shortname_file, "w", encoding='UTF-8') as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["name", "shortname"])
        writer.writerows(rows)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--loglevel',
        choices=('DEBUG', 'INFO', 'WARNING'),
        default='WARNING',
        help='loglevel [default: WARNING]',
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    logger.setLevel(args.loglevel)
    main(args)
