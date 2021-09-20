#!/usr/bin/env python3
# 恒常フリクエ・修練場のCSVデータをJSONファイルに変換
import json
from pathlib import Path
import csv
import unicodedata
import dataclasses
from typing import List
from tqdm import tqdm
import argparse
import logging
import requests

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

freequest_file = Path(__file__).resolve().parent / Path("freequest.csv")
freequest_json_file = Path(__file__).resolve().parent \
                      / "data/json" / Path("freequest.json")
drop_file = Path(__file__).resolve().parent / Path("hash_drop.json")
url_quest = "https://api.atlasacademy.io/nice/JP/quest/"

with open(drop_file, encoding='UTF-8') as f:
    drop_item = json.load(f)

FGOData_path = "../FGOData"
if Path(FGOData_path).exists() is False:
    FGOData_path = "../../FGOData"
viewQuestInfo_file = Path(FGOData_path) / "JP_tables/quest/viewQuestInfo.json"
with open(viewQuestInfo_file) as f:
    quest_info = json.load(f)

name2item = {}
shortname2name = {item["shortname"]: item["name"] for item in drop_item if "shortname" in item.keys()}
shortname2id = {item["shortname"]: item["id"] for item in drop_item if "shortname" in item.keys()}
shortname2dropPriority = {item["shortname"]: item["dropPriority"] for item in drop_item if "shortname" in item.keys()}
id2name = {item["id"]: item["name"] for item in drop_item if "name" in item.keys()}
id2type = {item["id"]: item["type"] for item in drop_item if "type" in item.keys()}
id2dropPriority = {item["id"]: item["dropPriority"] for item in drop_item if "dropPriority" in item.keys()}
questId2dropItemNum = {quest["questId"]: quest["dropSvtNum"] + quest["dropItemNum"] for quest in quest_info}
alias2id = {}
for item in drop_item:
    alias2id[unicodedata.normalize('NFKC', item["name"])] = item["id"]
    if "shortname" in item.keys():
        alias2id[unicodedata.normalize('NFKC', item["shortname"])] = item["id"]
    if "alias" in item.keys():
        for a in item["alias"]:
            alias2id[unicodedata.normalize('NFKC', a)] = item["id"]


class APIError(Exception):
    """
    API 呼び出しが失敗したことを示すエラー
    """


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
    dropItemNum: int


@dataclasses.dataclass(frozen=True)
class FgoFreeQuest(FgoQuest):
    scPriority: int

def questId2quest(questId):
    endpoint = f"{url_quest}{questId}/1"
    logger.info("calling HTTP API: %s", endpoint)
    r_get = requests.get(endpoint)
    if r_get.status_code != 200:
        raise APIError(f"status code: {r_get.status_code}, text: {r_get.text}")
    quest = r_get.json()
    return quest


def main(args):

    with open(freequest_file, encoding='UTF-8') as f:
        reader = csv.DictReader(f)
        tmps = [row for row in reader]

    quest_output = []
    for tmp in tqdm(tmps):
        # ドロップを作成
        drop = []
        for item in tmp.keys():
            if item.startswith("item"):
                if tmp[item] != "":
                    try:
                        item_id = shortname2id[tmp[item]]
                    except:
                        logger.critical('item: %s', item)
                        logger.critical('tmp[item]: %s', tmp[item])
                        exit()
                    name = id2name[item_id]
                    drop.append(DropItem(item_id, name, id2type[item_id],
                                         id2dropPriority[item_id]))

        drop = sorted(drop, key=lambda x: x.dropPriority, reverse=True)
        questId = int(tmp["id"])
        quest = questId2quest(questId)
        qp = quest["qp"]
        freequest = FgoFreeQuest(questId, tmp["quest"], tmp["place"],
                                 tmp["chapter"], qp, drop,
                                 questId2dropItemNum[questId],
                                 int(tmp['scPriority']))
        questname = quest["name"]
        if tmp["quest"] != questname:
            logger.warning("場所名が異なります%s %s", tmp["quest"], questname)
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
