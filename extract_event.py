#!/usr/bin/env python3
import json
from pathlib import Path
import csv

import requests

ID_OLD_EVENT_MAX = 94049000
id_exclude = (94052080, 94052507)

##kaemai_file = Path(__file__).resolve().parent / Path("kazemai.json")
mstQuest_url = "https://raw.githubusercontent.com/FZFalzar/FGOData/master/JP_tables/quest/mstQuest.json"

r_get2 = requests.get(mstQuest_url)

mstQuest_list = r_get2.json()

##print(mstItem_list)

##with open(kaemai_file, encoding='UTF-8') as f:
##    db = json.load(f)

q_list = []
for quest in mstQuest_list:
    if str(quest["id"]).startswith("94") and quest["id"] > ID_OLD_EVENT_MAX:
##        if id_exclude[0] > quest["id"] and id_exclude[1] < quest["id"]:
        if not (id_exclude[0] <= quest["id"] <= id_exclude[1]):
            q_list.append([quest["id"], quest["name"]])

with open("event_list.csv", "w", encoding='UTF-8') as f:
    writer = csv.writer(f, lineterminator="\n")
    writer.writerows(q_list)
