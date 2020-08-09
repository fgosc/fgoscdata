#!/usr/bin/env python3
# 恒常フリクエ・修練場のCSVデータをJSONファイルに変換
import json
from pathlib import Path
import csv
import mojimoji
import dataclasses
from typing import List
from tqdm import tqdm
import argparse
import logging


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

freequest_file = Path(__file__).resolve().parent / Path("freequest3.csv")
freequest_json_file = Path(__file__).resolve().parent / Path("freequest.json")
drop_file = Path(__file__).resolve().parent / Path("hash_drop.json")
kazemai_file = Path(__file__).resolve().parent / Path("kazemai3.json")

with open(drop_file, encoding='UTF-8') as f:
    drop_item = json.load(f)

with open(kazemai_file, encoding='UTF-8') as f:
    kazemai = json.load(f)

name2item = {}
shortname2name = {item["shortname"]:item["name"] for item in drop_item if "shortname" in item.keys()}
shortname2id = {item["shortname"]:item["id"] for item in drop_item if "shortname" in item.keys()}
shortname2dropPriority = {item["shortname"]:item["dropPriority"] for item in drop_item if "shortname" in item.keys()}
id2name = {item["id"]:item["name"] for item in drop_item if "name" in item.keys()}
id2type = {item["id"]:item["type"] for item in drop_item if "type" in item.keys()}
id2dropPriority = {item["id"]:item["dropPriority"] for item in drop_item if "dropPriority" in item.keys()}
spotid2spotname = {item["id"]:item["name"] for item in kazemai["mstSpot"]}
questId2spotid = {item["id"]:item["spotId"] for item in kazemai["mstQuest"]}
questId2qp = {item["questId"]:item["qp"] for item in kazemai["mstQuestPhase"]}
## questname2id = {item["chapter"] + " " + item["place"]:item["id"] for item in freequest}
alias2id = {}
for item in drop_item:
    alias2id[mojimoji.zen_to_han(mojimoji.han_to_zen(item["name"]), kana=False)] = item["id"]
    if "shortname"in item.keys():
        alias2id[mojimoji.zen_to_han(mojimoji.han_to_zen(item["shortname"]), kana=False)] = item["id"]
    if "alias"in item.keys():
        for a in item["alias"]:
            alias2id[mojimoji.zen_to_han(mojimoji.han_to_zen(a), kana=False)] = item["id"]

@dataclasses.dataclass(frozen=True)
class DropItem:
    """
    クエストのドロップアイテム
    """
    id: int
    name: str
    type: str
    dropPriority: int

@dataclasses.dataclass(frozen=True)
class FgoQuest:
    """
    クエスト情報
    """
    id: int
    name: str
    place: str
    chapter: str
    qp: int
    drop: List[DropItem]

@dataclasses.dataclass(frozen=True)
class FgoFreeQuest(FgoQuest):
    scPriority: int

def main(args):

    with open(freequest_file, encoding='UTF-8') as f:
        reader = csv.DictReader(f)
        tmps = [row for row in reader]

    quest_output = []
    for tmp in tqdm(tmps):
##        syutag_fq_story[tmp["クエスト名"]] = tmp["ストーリー"]
        # ドロップを作成
        drop = []
        for item in tmp.keys():
            if item.startswith("item"):
                if tmp[item] != "":
                    item_id = shortname2id[tmp[item]]
                    name = id2name[item_id]
                    drop.append(DropItem(item_id, name, id2type[item_id], id2dropPriority[item_id]))

##                    drop.append({"id":shortname2id[tmp[item]],
##                                 "name":shortname2name[tmp[item]],
##                                 "type":id2type[id],
##                                 "dropPriority":shortname2dropPriority[tmp[item]]})
        drop = sorted(drop, key=lambda x:x.dropPriority, reverse=True)
        questId = int(tmp["id"])
        qp = questId2qp[questId]
        freequest = FgoFreeQuest(questId, tmp["quest"], tmp["place"],
                             tmp["chapter"], qp, drop, int(tmp['scPriority']))
        spotname = mojimoji.zen_to_han(mojimoji.han_to_zen(spotid2spotname[questId2spotid[questId]]),kana=False)
        if tmp["place"] != spotname:
            logger.warning("場所名が異なります%s %s",tmp["place"], spotname)
        quest_output.append(dataclasses.asdict(freequest))
    
    with open(freequest_json_file, "w",  encoding='UTF-8') as f:
        f.write(json.dumps(quest_output, ensure_ascii=False, indent=4))


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

##        drop = sorted(drop, key=lambda x:x['dropPriority'],reverse=True)
##        name2item[tmp["クエスト名"]] = drop

##new_freequest = []
##for fq in freequest:
##    if fq["quest"] in syutag_fq_story.keys():
##        fq["category"] = syutag_fq_story[fq["quest"]]
##        fq["drop"] = name2item[fq["quest"]]
##    new_freequest.append(fq)

##new_freequest2 = []
##for fq in new_freequest:
##    if "category" not in fq.keys():
##        fq["category"] = "修練場"
##    new_freequest2.append(fq)

##syutag_syuren = []
##with open(syurenquest_file, encoding='UTF-8') as f:
##    reader = csv.DictReader(f)
##    tmps = [row for row in reader]
##    for tmp in tmps:
##        syutag_syuren.append(tmp["クエスト名"])
##        drop = []
##        for item in tmp.keys():
##            if item.startswith("アイテム"):
##                if tmp[item] != "":
##                    drop.append({"id":shortname2id[tmp[item]],
##                                 "name":shortname2name[tmp[item]],
##                                 "type":id2type[shortname2id[tmp[item]]],
##                                 "dropPriority":shortname2dropPriority[tmp[item]]})
##        drop = sorted(drop, key=lambda x:x['dropPriority'],reverse=True)        
##        name2item[tmp["クエスト名"]] = drop
##
##new_freequest2 = []
##for fq in freequest:
##    if fq["chapter"] + " " + fq["place"] in syutag_syuren:
##        fq["category"] = "修練場"
##        fq["drop"] = name2item[fq["chapter"] + " " + fq["place"]]
##    new_freequest2.append(fq)
##
##with open(new_freequest_json_file, 'w', encoding="UTF-8") as f:
##    f.write(json.dumps(new_freequest2, ensure_ascii=False, indent=4))
