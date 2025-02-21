from scoring.scorer import Scorer
import json

with open("data/valid_data.json", "r") as f:
    data = json.load(f)

with open("data/valid_label.json", "r") as f:
    gold_labels = json.load(f)

with open("results/prediction.json", "r") as f:
    predictions = json.load(f)

scorer = Scorer(
    data=data,
    predictions=predictions,
    gold_labels=gold_labels
)

print(scorer.get_scores())
