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

    def get_scores(self)->float:
        evaluation_dict = {
            "cov_ans": [0, 0], # [total, count]
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
        final_score_list = []
        cov_ans = None
        if evaluation_dict["cov_ans"][0] > 0:
            cov_ans = evaluation_dict["cov_ans"][1] / evaluation_dict["cov_ans"][0]
            final_score_list.append(cov_ans)
        risk_ans = None
        if evaluation_dict["risk_ans"][0] > 0:
            risk_ans = evaluation_dict["risk_ans"][1] / evaluation_dict["risk_ans"][0]
            final_score_list.append(1-risk_ans)
        risk_notans = None
        if evaluation_dict["risk_notans"][0] > 0:
            risk_notans = evaluation_dict["risk_notans"][1] / evaluation_dict["risk_notans"][0]
            final_score_list.append(1-risk_notans)
        
        for metric, eval_list in evaluation_dict.items():
            question_type = metric.split("_")[1]
            if eval_list[0] == 0:
                print(f"No data for {metric}. This happens when there is no `{question_type}` questions in the evaluation dataset. This metric will be ignored when calculating the final score. This will not happen when evaluating on the test set.")

        if len(final_score_list) == 0:
            raise AssertionError("No valid metrics to calculate the final score. This should not happen.")

        final_score = sum(final_score_list) / len(final_score_list) * 100
        scores_dict = {
            "cov_ans*100": round(cov_ans*100, 3) if cov_ans is not None else None,
            "risk_ans*100": round(risk_ans*100, 3) if risk_ans is not None else None,
            "risk_notans*100": round(risk_notans*100, 3) if risk_notans is not None else None,
            "final_score": round(final_score, 3)
        }
        print("="*100)
        print(f"Coverage for answerable questions (in %): {scores_dict['cov_ans*100']} || {evaluation_dict['cov_ans'][1]}/{evaluation_dict['cov_ans'][0]}")
        print(f"Risk for answerable questions (in %): {scores_dict['risk_ans*100']} || {evaluation_dict['risk_ans'][1]}/{evaluation_dict['risk_ans'][0]}")
        print(f"Risk for unanswerable questions (in %): {scores_dict['risk_notans*100']} || {evaluation_dict['risk_notans'][1]}/{evaluation_dict['risk_notans'][0]}")
        print(f"Final score: {scores_dict['final_score']}")
        print("="*100)
        # save the above information to a text file
        with open(os.path.join(self.score_dir, 'scores.txt'), 'w') as score_file:
            score_file.write(f"Coverage for answerable questions (in %): {scores_dict['cov_ans*100']} || {evaluation_dict['cov_ans'][1]}/{evaluation_dict['cov_ans'][0]}\n")
            score_file.write(f"Risk for answerable questions (in %): {scores_dict['risk_ans*100']} || {evaluation_dict['risk_ans'][1]}/{evaluation_dict['risk_ans'][0]}\n")
            score_file.write(f"Risk for unanswerable questions (in %): {scores_dict['risk_notans*100']} || {evaluation_dict['risk_notans'][1]}/{evaluation_dict['risk_notans'][0]}\n")
            score_file.write(f"Final score: {scores_dict['final_score']}\n")
    
        with open(os.path.join(self.score_dir, 'scores.json'), 'w') as score_file:
            score_file.write(json.dumps(scores_dict))
        return scores_dict


