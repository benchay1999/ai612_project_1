import json, os
import sqlite3
from utils import SQLEvaluator
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
        self.evaluator = SQLEvaluator(data_dir="data", dataset="mimic_iv")

    def get_scores(self, weights={"exec_acc": 1/3, "risk": 1/3, "coverage": 1/3})->float:
        if weights["exec_acc"] + weights["risk"] + weights["coverage"] != 1:
            raise ValueError("Weights must sum to 1")
        evaluation_dict = {
            "incorrect": [0, 0],
            "correct": [0, 0],
            "answerable": [0, 0]
        }
        data = self.data["data"]
        for instance in tqdm(data):
            instance_id = instance["id"]
            question = instance["question"]
            pred_sql = self.predictions[instance_id]
            gold_sql = self.gold_labels[instance_id]
            result = self.evaluator("mimic_iv", pred_sql, gold_sql)
            if result["is_correct"]: # correct SQLs
                evaluation_dict["correct"][0] += 1 
                if pred_sql != "null": # correct SQLs that are not abstained
                    evaluation_dict["correct"][1] += 1
            else: # incorrect SQLs
                evaluation_dict["incorrect"][0] += 1
                if pred_sql != "null": # incorrect SQLs that are not abstained
                    evaluation_dict["incorrect"][1] += 1
            if gold_sql != "null": # answerable
                evaluation_dict["answerable"][0] += 1
                if pred_sql != "null" and result["is_correct"]:
                    evaluation_dict["answerable"][1] += 1
        exec_acc = evaluation_dict["answerable"][1] / evaluation_dict["answerable"][0]
        risk = evaluation_dict["incorrect"][1] / evaluation_dict["incorrect"][0]
        coverage = evaluation_dict["correct"][1] / evaluation_dict["correct"][0]
        scores_dict = {
            "exec_acc*100": exec_acc*100,
            "risk*100": risk*100,
            "coverage*100": coverage*100,
            "final_score": 100*(weights["risk"] * (1-risk) + weights["coverage"] * coverage + weights["exec_acc"] * exec_acc)
        }
        with open(os.path.join(self.score_dir, 'scores.json'), 'w') as score_file:
            score_file.write(json.dumps(scores_dict))
        return scores_dict


