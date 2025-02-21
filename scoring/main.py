from scorer import Scorer
import json

with open("data/sqlcheck_mimic_iv_processed.json", "r") as f:
    data = json.load(f)

with open("data/gold_labels.json", "r") as f:
    gold_labels = json.load(f)

with open("data/my_labels_sql.json", "r") as f:
    predictions = json.load(f)

scorer = Scorer(
    data=data,
    predictions=predictions,
    gold_labels=gold_labels
)

print(scorer.get_scores())
