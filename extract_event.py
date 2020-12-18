#!/usr/bin/env python3
import json
from pathlib import Path
import csv
import argparse
import datetime
import logging

import requests

logger = logging.getLogger(__name__)

mstQuest_url = "https://raw.githubusercontent.com/FZFalzar/FGOData/master/JP_tables/quest/mstQuest.json"
mstQuestInfo_url = "https://raw.githubusercontent.com/FZFalzar/FGOData/master/JP_tables/quest/viewQuestInfo.json"


def main(args):
    opened = int(datetime.datetime.strptime(args.openedat, "%Y/%m/%d").timestamp())
    closed = int(datetime.datetime.strptime(args.closedat + ' 23:59:59', "%Y/%m/%d %H:%M:%S").timestamp())
    logger.debug("opendat: %s", opened)
    logger.debug("closedat: %s", closed)

    r_get = requests.get(mstQuest_url)
    mstQuest_list = r_get.json()
    r_get2 = requests.get(mstQuestInfo_url)
    mstQuestInfo_list = r_get2.json()

    q_list = []
    for quest in mstQuest_list:
        if opened <= quest["openedAt"] and quest["closedAt"] <= closed:
            for q in mstQuestInfo_list:
                if q["questId"] == quest["id"] and "高難易度" not in quest["name"]:
                    q_list.append([quest["id"], quest["name"], quest["recommendLv"]])
                    break

    with open("event_list.csv", "w", encoding='UTF-8') as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerows(q_list)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FGOクエストをCSV出力')
    parser.add_argument('-o', '--openedat',
                        required=True,
                        help='quest open date: e.g. 2015/7/30')
    parser.add_argument('-c', '--closedat',
                        required=True,
                        help='quest close date: e.g.  2020/11/03')
    parser.add_argument('-l', '--loglevel',
                        choices=('debug', 'info'), default='info')
    args = parser.parse_args()    # 引数を解析
    lformat = '[%(levelname)s] %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=lformat,
    )
    logger.setLevel(args.loglevel.upper())
    main(args)