#!/usr/bin/env python3
# イベントCSVデータをJSONファイルに変換
import argparse
import csv
import dataclasses
import json
import logging
import unicodedata
from pathlib import Path

import requests

from make_freequest import (
    DropItem,
    FgoQuest,
    alias2id,
    fetch_free_quests,
    id2dropPriority,
    id2name,
    id2type,
)

url = "https://api.atlasacademy.io/export/JP/nice_war.json"

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

csv_dir = Path(__file__).resolve().parent / Path("data/csv/")
json_dir = Path(__file__).resolve().parent / Path("data/json/")


@dataclasses.dataclass(frozen=True)
class FgoEventQuest(FgoQuest):
    shortname: str


# ---------------------------------------------------------
# UTF-8 BOM 判定
# ---------------------------------------------------------
def open_file_with_utf8(filename):
    is_with_bom = is_utf8_file_with_bom(filename)
    encoding = "utf-8-sig" if is_with_bom else "utf-8"
    return open(filename, encoding=encoding)


def is_utf8_file_with_bom(filename):
    line_first = open(filename, encoding="utf-8").readline()
    return line_first.startswith("\ufeff")


# ---------------------------------------------------------
# Quest データ取得の抽象化（ファイル or API）
# ---------------------------------------------------------
class QuestSource:
    """nice_war.json が読めない場合、または questId が存在しない場合 API にフォールバック"""

    def __init__(self, url):
        self.url = url
        self.free_quests = None
        self.api_cache = {}  # API 連打防止

        self._load()

    def _load(self):
        try:
            self.free_quests = fetch_free_quests(self.url)
            logger.info("Loaded nice_war.json successfully")
        except Exception as e:
            logger.error("Failed to load nice_war.json: %s", e)
            logger.warning("Switching to API fallback mode")
            self.free_quests = None

    def get(self, quest_id: int):
        """quest_id に対応するデータを返す。
        - nice_war.json に存在すればそれを使う
        - 存在しなければ API にフォールバック
        """
        # ファイルが読めている場合
        if self.free_quests is not None:
            q = self.free_quests.get(quest_id)
            if q is not None:
                return q
            # ← ここが今回の重要修正点
            logger.warning(
                "Quest %s not found in nice_war.json → API fallback", quest_id
            )

        # API fallback
        return self._fetch_single_quest(quest_id)

    def _fetch_single_quest(self, quest_id: int):
        if quest_id in self.api_cache:
            return self.api_cache[quest_id]

        api_url = f"https://api.atlasacademy.io/nice/JP/quest/{quest_id}"
        try:
            r = requests.get(api_url, timeout=10)
            r.raise_for_status()
            data = r.json()

            q = {
                "recommendLv": data.get("recommendLv", "0"),
                "name": data.get("name", ""),
            }
            self.api_cache[quest_id] = q
            return q

        except Exception as e:
            logger.error("API fetch failed for quest %s: %s", quest_id, e)
            return None


# ---------------------------------------------------------
# メイン処理
# ---------------------------------------------------------
def list2dic(quest_list):
    source = QuestSource(url)
    quest_output = []

    for quest in quest_list:
        # -----------------------------
        # ドロップ処理
        # -----------------------------
        drop = []
        for item in quest.keys():
            if item.startswith("item") and quest[item] != "":
                quest[item] = unicodedata.normalize("NFKC", quest[item])
                if quest[item] not in alias2id:
                    logger.error("Error: 変換できません: %s", quest[item])
                    exit(1)

                item_id = alias2id[quest[item]]
                name = id2name[item_id]
                id2_type = id2type[item_id]
                drop_priority = id2dropPriority[item_id]

                if id2_type == "Craft Essence":
                    drop_priority *= 10

                drop.append(DropItem(item_id, name, id2_type, drop_priority))

        drop = sorted(drop, key=lambda x: x.dropPriority, reverse=True)

        # -----------------------------
        # Quest データ取得（ファイル or API）
        # -----------------------------
        questId = int(quest["id"])
        q = source.get(questId)

        if q is None:
            logger.error("Quest data not found for id=%s", questId)
            continue

        # -----------------------------
        # QP 計算
        # -----------------------------
        lv = q["recommendLv"]
        if lv == "90++":
            qp = 13536
        elif lv == "90+++":
            qp = 16244
        elif lv == "90+":
            qp = 11280
        elif lv == "120★★★":
            qp = 558187
        else:
            try:
                qp = int(lv) * 100 + 400
            except:
                qp = 0

        spotname = q["name"]

        # -----------------------------
        # 出力データ構築
        # -----------------------------
        event_quest = FgoEventQuest(
            questId,
            quest["quest"],
            "",
            "",
            "",
            qp,
            drop,
            -1,  # dropItemNum
            quest["shortname"],
        )

        if quest["quest"] != spotname:
            logger.warning("場所名が異なります: %s %s", quest["quest"], spotname)

        quest_output.append(dataclasses.asdict(event_quest))

    return quest_output


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------
def main(args):
    file = Path(args.csv)
    if not file.exists():
        logger.critical("File not found: %s", file)
        exit(1)

    with open_file_with_utf8(file) as f:
        reader = csv.DictReader(f)
        quest_list = [row for row in reader]

    quest_dic = list2dic(quest_list)

    outfile = json_dir / (file.stem + ".json")
    with open(outfile, "w", encoding="UTF-8") as f:
        f.write(json.dumps(quest_dic, ensure_ascii=False, indent=4))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", help="input csv file")
    parser.add_argument(
        "--loglevel",
        choices=("DEBUG", "INFO", "WARNING"),
        default="WARNING",
        help="loglevel [default: WARNING]",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logger.setLevel(args.loglevel)
    main(args)
