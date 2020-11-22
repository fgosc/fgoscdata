#!/usr/bin/env python3
import argparse
import logging
import json
from pathlib import Path
import csv
import unicodedata
import re

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

item_url = "https://api.atlasacademy.io/export/JP/nice_item.json"
ce_url = "https://api.atlasacademy.io/export/JP/nice_equip.json"
Item_blacklist_file = Path(__file__).resolve().parent / Path("item_bl.txt")
shortname_file = Path(__file__).resolve().parent / Path("shortname.csv")
CE_blacklist_file = Path(__file__).resolve().parent / Path("ce_bl.txt")
CE_gacha_file = Path(__file__).resolve().parent / Path("ce_gacha.txt")
ces = []

def parse_page(load_url):
    html = requests.get(load_url)
    soup = BeautifulSoup(html.content, "html.parser")
    page_title = soup.find('title')
    if "ピックアップ召喚" not in page_title.get_text():
        return []
    ces = []
    items = soup.select(".gainen_ttl")
    for item in items:
        text = unicodedata.normalize('NFKC', item.get_text())
        text =re.sub("\([^\(\)]*\)$", "", text.strip()).strip()
        ces.append(text)
    return ces


def get_pages():
    base_url = "https://news.fate-go.jp"
    html = requests.get(base_url)
    soup = BeautifulSoup(html.content, "html.parser")
    tag_item = soup.select('ul.list_news li a')
    ces = []

    for tag in tag_item:
        load_url = base_url + tag.get("href")
        logger.debug(load_url)
        try:
            ce_list = parse_page(load_url)
        except Exception as e:
            logger.exception(e)
            ce_list = None
        if ce_list is not None:
            ces += ce_list
    return ces

def is_gachaCe(ce):
    """
    ガチャ産CEか判別
    """
    if ce in ces:
        return True
    else:
        return False


def main(args):
    global ces
    ces = get_pages()
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
        # 公式ウェブのピックアップ召喚情報にある概念礼装を除外
        if is_gachaCe(ce["name"]):
            gacha_ces.append(ce["name"])
            continue
        if ce["name"] not in name2shortname.keys():
            name2shortname[ce["name"]] = ""

    rows = [[k, v] for k, v in name2shortname.items()]
    with open(shortname_file, "w", encoding='UTF-8') as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["name", "shortname"])
        writer.writerows(rows)
    with open(CE_gacha_file, "w", encoding='UTF-8') as f:
        f.write('\n'.join(gacha_ces))


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
