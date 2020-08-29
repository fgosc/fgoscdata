#!/usr/bin/env python3
# イベントidから同一のイベントid群を抽出
import json
import argparse
import logging
import requests

url_quest = "https://api.atlasacademy.io/nice/JP/quest/"

mstQuest_url = "https://raw.githubusercontent.com/FZFalzar/FGOData/master/JP_tables/quest/mstQuest.json"

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def main(args):
    questid_start = int(args.questid / 100)*100 + 1
    questid_end = int(args.questid / 100)*100 + 99
    r_get = requests.get(mstQuest_url)
    mstQuest_list = r_get.json()
    logger.debug("mstQuest_list: %s", mstQuest_list)
    for quest in mstQuest_list:
        if questid_start <= quest["id"] <= questid_end:
            print("{},{}".format(quest["id"], quest["name"]))

def parse_args():
    parser = argparse.ArgumentParser(description='questidからそのイベントのクエストをリストする')
    parser.add_argument(
        'questid',
        type=int,
        help='id of quest in FGO game data (e.g. 94051711)',
    )
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
