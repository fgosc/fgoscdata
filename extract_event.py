#!/usr/bin/env python3
import json
from pathlib import Path
import csv

kaemai_file = Path(__file__).resolve().parent / Path("kazemai.json")

with open(kaemai_file, encoding='UTF-8') as f:
    db = json.load(f)

q_list = []
for quest in db["mstQuest"]:
    if str(quest["id"]).startswith("94"):
        q_list.append([quest["id"], quest["name"]])

with open("all_fq_list.csv", "w", encoding='UTF-8') as f:
    writer = csv.writer(f, lineterminator="\n")
    writer.writerows(q_list)
