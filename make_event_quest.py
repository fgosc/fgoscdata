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
from make_freequest import DropItem, FgoQuest, questId2qp

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

csv_dir = Path(__file__).resolve().parent / Path("data/csv/")
json_dir = Path(__file__).resolve().parent / Path("data/json/")


@dataclasses.dataclass(frozen=True)
class FgoEventQuest(FgoQuest):
    shortname: str


def main(args):
    infiles = csv_dir.glob('**/*.csv')

    for infile in tqdm(infiles):
        # 各ファイルを処理

        with open(infile, encoding='UTF-8') as f:
            reader = csv.DictReader(f)
            tmps = [row for row in reader]

        quest_output = []
        for tmp in tmps:
            # ドロップを作成
            drop = []
            for item in tmp.keys():
                if item.startswith("item"):
                    if tmp[item] != "":
                        tmp[item] = unicodedata.normalize("NFKC", tmp[item])
                        if tmp[item] in alias2id.keys():
                            item_id = alias2id[tmp[item]]
                        else:
                            logger.warning("Error: 変換できません: %s", tmp[item])
                            exit(1)
                        name = id2name[alias2id[tmp[item]]]
                        drop.append(DropItem(item_id, name, id2type[item_id],
                                             id2dropPriority[item_id]))

            drop = sorted(drop, key=lambda x: x.dropPriority, reverse=True)
            questId = int(tmp["id"])
            qp = questId2qp[questId]
            logger.debug('drop: %s', drop)
            event_quest = FgoEventQuest(int(tmp["id"]), tmp["quest"],
                                        "", "", qp, drop, tmp["shortname"])

            quest_output.append(dataclasses.asdict(event_quest))

        outfile = json_dir / (infile.stem + ".json")
        with open(outfile, "w",  encoding='UTF-8') as f:
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
