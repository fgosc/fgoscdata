#!/usr/bin/env python3
# イベントCSVデータをJSONファイルに変換
import argparse
import dataclasses
import logging
import json
from pathlib import Path
import csv
import unicodedata
from tqdm import tqdm
from make_freequest import id2name, id2type, id2dropPriority, alias2id
# from make_freequest import questId2dropItemNum
from make_freequest import DropItem, FgoQuest, questId2quest

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

csv_dir = Path(__file__).resolve().parent / Path("data/csv/")
json_dir = Path(__file__).resolve().parent / Path("data/json/")


@dataclasses.dataclass(frozen=True)
class FgoEventQuest(FgoQuest):
    shortname: str


def open_file_with_utf8(filename):
    '''utf-8 のファイルを BOM ありかどうかを自動判定して読み込む
    '''
    is_with_bom = is_utf8_file_with_bom(filename)

    encoding = 'utf-8-sig' if is_with_bom else 'utf-8'

    return open(filename, encoding=encoding)


def is_utf8_file_with_bom(filename):
    '''utf-8 ファイルが BOM ありかどうかを判定する
    '''
    line_first = open(filename, encoding='utf-8').readline()
    return (line_first[0] == '\ufeff')


def list2dic(quest_list):
    quest_output = []
    for quest in quest_list:
        # ドロップを作成
        drop = []
        for item in quest.keys():
            if item.startswith("item"):
                if quest[item] != "":
                    quest[item] = unicodedata.normalize("NFKC", quest[item])
                    if quest[item] in alias2id.keys():
                        item_id = alias2id[quest[item]]
                    else:
                        logger.error("Error: 変換できません: %s", quest[item])
                        exit(1)
                    name = id2name[alias2id[quest[item]]]
                    drop.append(DropItem(item_id, name, id2type[item_id],
                                         id2dropPriority[item_id]))

        drop = sorted(drop, key=lambda x: x.dropPriority, reverse=True)
        questId = int(quest["id"])
        q = questId2quest(questId)
        if q["recommendLv"] == "90++":
            qp = 13536
        elif q["recommendLv"] == "90+++":
            qp = 16243
        elif q["recommendLv"] == "90+":
            qp = 11280
        else:
            qp = int(q["recommendLv"])*100 + 400
        spotname = q["name"]
        logger.debug('drop: %s', drop)
        # try:
        #     dropItemNum = questId2dropItemNum[questId]
        # except:
        #     logger.warning("ドロップ枠数が取得できません")
        #     dropItemNum = -1
        dropItemNum = -1
        event_quest = FgoEventQuest(int(quest["id"]), quest["quest"],
                                    "", "", "", qp, drop,
                                    dropItemNum,
                                    quest["shortname"])
        if quest["quest"] != spotname:
            logger.warning("場所名が異なります: %s %s",
                           quest["quest"], spotname)
        
        quest_output.append(dataclasses.asdict(event_quest))
    return quest_output

def main(args):
    file = Path(args.csv)
    if file.exists() is False:
        logger.critical("File not found: %s", file)
        exit(1)

    with open_file_with_utf8(file) as f:
        reader = csv.DictReader(f)
        quest_list = [row for row in reader]

    quest_dic = list2dic(quest_list)

    outfile = json_dir / (file.stem + ".json")
    with open(outfile, "w",  encoding='UTF-8') as f:
        f.write(json.dumps(quest_dic, ensure_ascii=False, indent=4))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'csv',
        help='input csv file',
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
