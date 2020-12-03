#!/usr/bin/env python3
import json
from pathlib import Path
import csv
import argparse
import datetime
import logging
import unicodedata

import requests

logger = logging.getLogger(__name__)

mstQuest_url = "https://raw.githubusercontent.com/FZFalzar/FGOData/master/JP_tables/quest/mstQuest.json"
# mstQuestInfo_url = "https://raw.githubusercontent.com/FZFalzar/FGOData/master/JP_tables/quest/viewQuestInfo.json"
mstSpot_url = "https://raw.githubusercontent.com/FZFalzar/FGOData/master/JP_tables/spot/mstSpot.json"
mstWar_url = "https://raw.githubusercontent.com/FZFalzar/FGOData/master/JP_tables/war/mstWar.json"
mstQuestPhase_url = "https://raw.githubusercontent.com/FZFalzar/FGOData/master/JP_tables/quest/mstQuestPhase.json"

def main(args):
    r_get = requests.get(mstQuest_url)
    mstQuest_list = r_get.json()
    r_get2 = requests.get(mstSpot_url)
    mstSpot_list = r_get2.json()
    spotid2name = {spot["id"]: spot["name"] for spot in mstSpot_list}
    sportid2warId = {spot["id"]: spot["warId"] for spot in mstSpot_list}
    r_get3 = requests.get(mstWar_url)
    mstWar_list = r_get3.json()
    warId2name = {war["id"]: war["longName"].split(" ")[-1] for war in mstWar_list}
    r_get4 = requests.get(mstQuestPhase_url)
    mstQuestPhase_list = r_get4.json()
    id2bond = {quest["questId"]: quest["friendshipExp"] for quest in mstQuestPhase_list}

    q_list = []
    q_category = {9300:"フリクエ1部", 9302:"フリクエ1.5部", 9303:"フリクエ2部"}
    for quest in mstQuest_list:
        q_dic = {}
        # if opened <= quest["openedAt"] and quest["closedAt"] <= closed:
        #     for q in mstQuestInfo_list:
        #         if q["questId"] == quest["id"] and "高難易度" not in quest["name"]:
        #             q_list.append([quest["id"], quest["name"]])
        #             break
        # id	category	chapter	place	quest	scPriority
        if  93000001 <= quest["id"] <= 93900001:
            if quest["afterClear"] == 3:
                q_dic["id"] = quest["id"]
                q_dic["sort_id"] = int(quest["id"]/100)
                q_dic["category"] = q_category[int(quest["id"]/10000)]
                q_dic["chapter"] = warId2name[sportid2warId[quest["spotId"]]]
                if q_dic["chapter"] == "イ・プルーリバス・ウナム":
                    q_dic["chapter"] = "北米"
                q_dic["place"] = unicodedata.normalize('NFKC', spotid2name[quest["spotId"]])
                q_dic["quest"] = unicodedata.normalize('NFKC', quest["name"])
                q_dic["bond_per_ap"] = id2bond[quest["id"]]/quest["actConsume"]
                q_list.append(q_dic)
    q_list = sorted(q_list, key=lambda x: (x['sort_id'], x['bond_per_ap'], x['id']))
    q_list_new = []
    scPriority = 1001
    for q in q_list:
        del q["sort_id"], q["bond_per_ap"]
        q["scPriority"] = scPriority
        q_list_new.append(q)
        scPriority += 1

    with open("freequest_tmp.csv", "w", encoding='UTF-8') as f:
        # writer = csv.DictWriter(f, ['id', "sort_id", 'category', 'chapter', 'place', 'quest', "bond_per_ap"], lineterminator="\n")
        writer = csv.DictWriter(f, ['id', 'category', 'chapter', 'place', 'quest', 'scPriority'], lineterminator="\n")
        writer.writeheader()
        # writer = csv.writer(f, lineterminator="\n")
        writer.writerows(q_list_new)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FGOクエストをCSV出力')
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