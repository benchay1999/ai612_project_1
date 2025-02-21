import json, os
import sqlite3
from scoring.utils import SQLEvaluator
from tqdm import tqdm
class Scorer:
    def __init__(
        self, 
        data, 
        predictions,
        gold_labels,
        score_dir="."
    ):
        self.data = data
        self.predictions = predictions
        self.gold_labels = gold_labels
        self.score_dir = score_dir
        self.evaluator = SQLEvaluator(data_dir="database", dataset="mimic_iv")

    def get_scores(self, weights={"cov_ans": 1/3, "risk_ans": 1/3, "risk_notans": 1/3})->float:
        if weights["cov_ans"] + weights["risk_ans"] + weights["risk_notans"] != 1:
            raise ValueError("Weights must sum to 1")
        evaluation_dict = {
            "cov_ans": [0, 0],
            "risk_ans": [0, 0],
            "risk_notans": [0, 0]
        }
        data = self.data["data"]
        for instance in tqdm(data[:40]):
            instance_id = instance["id"]
            question = instance["question"]
            pred_sql = self.predictions[instance_id]
            gold_sql = self.gold_labels[instance_id]
            result = self.evaluator("mimic_iv", pred_sql, gold_sql)
            if gold_sql != "null": # answerable
                evaluation_dict["cov_ans"][0] += 1
                evaluation_dict["risk_ans"][0] += 1
                if pred_sql != "null": # not abstained
                    evaluation_dict["cov_ans"][1] += 1 # not abstained answerable
                    if not result["is_correct"]:
                        evaluation_dict["risk_ans"][1] += 1 # not abstained answerable incorrect
            else: # unanswerable
                evaluation_dict["risk_notans"][0] += 1
                if pred_sql != "null": 
                    evaluation_dict["risk_notans"][1] += 1 # not abstained unanswerable
                
        cov_ans = 0
        if evaluation_dict["cov_ans"][0] > 0:
            cov_ans = evaluation_dict["cov_ans"][1] / evaluation_dict["cov_ans"][0]
        risk_ans = 0
        if evaluation_dict["risk_ans"][0] > 0:
            risk_ans = evaluation_dict["risk_ans"][1] / evaluation_dict["risk_ans"][0]
        risk_notans = 0
        if evaluation_dict["risk_notans"][0] > 0:
            risk_notans = evaluation_dict["risk_notans"][1] / evaluation_dict["risk_notans"][0]
        scores_dict = {
            "cov_ans*100": round(cov_ans*100, 3),
            "risk_ans*100": round(risk_ans*100, 3),
            "risk_notans*100": round(risk_notans*100, 3),
            "final_score": round(100*(weights["risk_ans"] * (1-risk_ans) + weights["risk_notans"] * (1-risk_notans) + weights["cov_ans"] * cov_ans), 3)
        }
        with open(os.path.join(self.score_dir, 'scores.json'), 'w') as score_file:
            score_file.write(json.dumps(scores_dict))
        return scores_dict


