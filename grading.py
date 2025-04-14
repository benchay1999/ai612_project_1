from scoring.scorer import Scorer
import json
import os
with open("data/test_data.json", "r") as f:
    data = json.load(f)

with open("../test_label.json", "r") as f:
    gold_labels = json.load(f)

for file in os.listdir("submissions"):
    if file.endswith(".json"):
        with open(f"submissions/{file}", "r") as f:
            predictions = json.load(f)
        team_name = file.split("file_")[-1].replace(".json","")
        print(team_name)
        if not os.path.exists(f'results/{team_name}'):
            os.makedirs(f'results/{team_name}')
        try:
            scorer = Scorer(
                data=data,
                predictions=predictions,
                gold_labels=gold_labels,
                score_dir=f'results/{team_name}'
            )

            print(scorer.get_scores())
        except:
            print(f"Error in {team_name}")
