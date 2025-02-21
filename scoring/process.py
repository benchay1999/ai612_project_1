import json

#with open("data/my_labels.json", "r") as f:
#    data = json.load(f)
#
#result = {key: label_dict["sql"] for key, label_dict in data.items()}
#with open("data/my_labels_sql.json", "w") as f:
#    json.dump(result, f)

#with open("data/sqlcheck_mimic_iv.json", "r") as f:
#    data = json.load(f)
#
#result = {"data": [{"id": instance["id"], "question": instance["question"]} for instance in data]}
#
#with open("data/sqlcheck_mimic_iv_processed.json", "w") as f:
#    json.dump(result, f)


with open("data/sqlcheck_mimic_iv.json", "r") as f:
    data = json.load(f)

result = {sample["id"]: sample["query"] for sample in data}
with open("data/gold_labels.json", "w") as f:
    json.dump(result, f)