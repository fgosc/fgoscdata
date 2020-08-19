#!/usr/bin/env python3
# 恒常フリクエ・修練場のCSVデータをJSONファイルに変換
import json
import argparse
import logging
import requests

url_quest = "https://api.atlasacademy.io/nice/JP/quest/"

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def main(args):
    questid_start = int(args.questid / 100)*100 + 1
    for i in range(99):
        r_get = requests.get(url_quest + str(questid_start + i) + "/1")
        if r_get.status_code == 404:
            break
        quest = r_get.json()
        logger.debug("quest: %s", quest)
        print("{},{}".format(questid_start + i, quest["name"]))

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
