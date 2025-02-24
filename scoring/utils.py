import json, os
import re
from func_timeout import func_timeout, FunctionTimedOut
import sqlite3
import numpy as np
CURRENT_DATE = "2100-12-31"
CURRENT_TIME = "23:59:00"
NOW = f"{CURRENT_DATE} {CURRENT_TIME}"
PRECOMPUTED_DICT = {
    'temperature': (35.5, 38.1),
    'sao2': (95.0, 100.0),
    'heart rate': (60.0, 100.0),
    'respiration': (12.0, 18.0),
    'systolic bp': (90.0, 120.0),
    'diastolic bp': (60.0, 90.0),
    'mean bp': (60.0, 110.0)
}
TIME_PATTERN = r"(DATE_SUB|DATE_ADD)\((\w+\(\)|'[^']+')[, ]+ INTERVAL (\d+) (MONTH|YEAR|DAY)\)"

def process_item(item, db_id):
    try:
        item = round(float(item),3)
    except:
        pass
    return str(item)

def process_answer(ans, db_id):
    if type(ans)==str: # null
        return ans
    else:
        return str(sorted([[process_item(c, db_id) for c in row] for row in ans])[:100]) # check only up to 100th record


def normalize_sql_spacing(query):
    
    values = extract_sql_strings(query)
    for idx, val in enumerate(values):
        query = query.replace(val, f'__PLACEHOLDER{idx}__')
    
    # postprocess remove spaces around brackets
    query = re.sub(r'\s*\(\s*', '(', query)
    query = re.sub(r'\s*\)\s*', ') ', query)
    query = re.sub(r'\s*,\s*', ', ', query)
    
    for idx, val in enumerate(values):
        query = query.replace(f'__PLACEHOLDER{idx}__', val)
    
    return query.strip()

def postprocess_gt(query, db_id):
    '''
    Postprocessing for ground-truth SQL
    '''
    if 'select' not in query.lower(): # remove non-select queries
        return 'null'

    if "current_time" in query: # strftime('%J',current_time) => strftime('%J','2100-12-31 23:59:00')
        query = query.replace("current_time", f"'{NOW}'")
    if re.search('[ \n]+([a-zA-Z0-9_]+_lower)', query) and re.search('[ \n]+([a-zA-Z0-9_]+_upper)', query): # systolic_bp_lower => 90.0
        vital_lower_expr = re.findall('[ \n]+([a-zA-Z0-9_]+_lower)', query)[0]
        vital_upper_expr = re.findall('[ \n]+([a-zA-Z0-9_]+_upper)', query)[0]
        vital_name_list = list(set(re.findall('([a-zA-Z0-9_]+)_lower', vital_lower_expr) + re.findall('([a-zA-Z0-9_]+)_upper', vital_upper_expr)))
        if len(vital_name_list) == 1:
            processed_vital_name = vital_name_list[0].replace('_', ' ')
            if processed_vital_name in PRECOMPUTED_DICT:
                vital_range = PRECOMPUTED_DICT[processed_vital_name]
                query = query.replace(vital_lower_expr, f"{vital_range[0]}").replace(vital_upper_expr, f"{vital_range[1]}")
    query = query.replace("%y", "%Y").replace('%j', '%J') # strftime('%y-%m',outputevents.charttime) => strftime('%Y-%m',outputevents.charttime)

    return query

def postprocess_pred(query, db_id):
    '''
    Postprocessing for predicted SQL. Modify if necessary.
    '''
    if 'select' not in query.lower(): # remove non-select queries
        return 'null'
    
    query = query.replace('```sql', '').replace('```', '') # function calling filtering
    query = query.replace('> =', '>=').replace('< =', '<=').replace('! =', '!=') # tokenization adjustment for open-source models
    query = re.sub('[ ]+', ' ', query.replace('\n', ' ')).strip()

    # postprocess string literals
    if db_id in ['atis', 'advising']: # => "
        pattern = r"'([^']*)'"
        query = re.sub(pattern, r'"\1"', query)
    else: # => '
        pattern = r'"([^\']*)"'
        query = re.sub(pattern, r"'\1'", query)

    if "current_time" in query: # strftime('%J',current_time) => strftime('%J','2100-12-31 23:59:00')
        query = query.replace("current_time", f"'{NOW}'")
    if "'now'" in query: # 'now' => '2100-12-31 23:59:00'
        query = query.replace("'now'", f"'{NOW}'")
    if "NOW()" in query: # NOW() => '2100-12-31 23:59:00'
        query = query.replace("NOW()", f"'{NOW}'")
    if "CURDATE()" in query: # CURDATE() => '2100-12-31'
        query = query.replace("CURDATE()", f"'{CURRENT_DATE}'")
    if "CURTIME()" in query: # CURTIME() => '23:59:00'
        query = query.replace("CURTIME()", f"'{CURRENT_TIME}'")

    if re.search('[ \n]+([a-zA-Z0-9_]+_lower)', query) and re.search('[ \n]+([a-zA-Z0-9_]+_upper)', query): # systolic_bp_lower => 90.0
        vital_lower_expr = re.findall('[ \n]+([a-zA-Z0-9_]+_lower)', query)[0]
        vital_upper_expr = re.findall('[ \n]+([a-zA-Z0-9_]+_upper)', query)[0]
        vital_name_list = list(set(re.findall('([a-zA-Z0-9_]+)_lower', vital_lower_expr) + re.findall('([a-zA-Z0-9_]+)_upper', vital_upper_expr)))
        if len(vital_name_list) == 1:
            processed_vital_name = vital_name_list[0].replace('_', ' ')
            if processed_vital_name in PRECOMPUTED_DICT:
                vital_range = PRECOMPUTED_DICT[processed_vital_name]
                query = query.replace(vital_lower_expr, f"{vital_range[0]}").replace(vital_upper_expr, f"{vital_range[1]}")
    query = query.replace("%y", "%Y").replace('%j', '%J') # strftime('%y-%m',outputevents.charttime) => strftime('%Y-%m',outputevents.charttime)

    return query


def modify_distinct(pred, real):
    if not isinstance(pred, str):
        pred = str(pred)

    # Early returns if conditions are not met
    if pred.lower() == 'null' or real.lower() == 'null' or 'select' not in pred.lower():
        return pred

    # Define regex patterns to check the presence of DISTINCT right after SELECT.
    # We'll ignore case differences and assume the top-level SELECT is at the start of the query.
    select_distinct_pattern = re.compile(r"(?i)\bSELECT\s+DISTINCT\b")
    select_pattern = re.compile(r"(?i)\bSELECT\b")

    # Check if gold_sql has DISTINCT
    gold_has_distinct = bool(select_distinct_pattern.search(real))
    pred_has_distinct = bool(select_distinct_pattern.search(pred))

    if gold_has_distinct and not pred_has_distinct:
        # Gold requires DISTINCT, but pred doesn't have it. Insert DISTINCT right after SELECT.
        # Replace the first occurrence of SELECT (not DISTINCT), ensuring we don't double insert.
        if select_distinct_pattern.search(pred):
            # Already has DISTINCT, do nothing
            pass
        else:
            # Insert DISTINCT after SELECT
            pred = select_pattern.sub("SELECT DISTINCT", pred, count=1)
    elif not gold_has_distinct and pred_has_distinct:
        # Gold does not have DISTINCT, but pred does. Remove DISTINCT.
        # Replace 'SELECT DISTINCT' with 'SELECT'
        pred = select_distinct_pattern.sub("SELECT", pred, count=1)

    return pred

def execute_sql_for_evaluator(sql, db_path):
    con = sqlite3.connect(db_path)
    con.text_factory = lambda b: b.decode(errors="ignore")
    cur = con.cursor()
    try:
        result = cur.execute(sql).fetchmany(10)
    except Exception as e:
        result = f"[Error] Error in executing SQL: {e}\nSQL: {sql}\n"
    con.close()
    return result

class SQLEvaluator:
    def __init__(self, data_dir: str, dataset: str):
        self.data_dir = data_dir
        self.dataset = dataset
        self.table_path = f"{data_dir}/tables.json"
        try:
            with open(self.table_path, "r") as f:
                self.tables = json.load(f)
        except Exception as e:
            raise ValueError(f"Error in loading tables.json: {e}")
        self.column_names = [column[1] for db in self.tables if db['db_id'] == self.dataset for column in db['column_names_original']]
    def get_gold_columns_only(self, sql: str):
        """
        Gets column names from the SQL query.

        Args:
            sql (str): SQL query

        Returns:
            column_list (list): list of column names
        """
        try:
            # Parse the SQL query
            parsed = parse_one(sql, read='sqlite', error_level='ignore')#parse_one(sql)
            
            # Extract all column references
            columns = parsed.find_all(exp.Column,)
            # Get unique column names, ignoring table names
            column_list = list(set(col.name for col in columns))
            column_list = [column for column in column_list if not column.endswith('id') and column in self.column_names]
            return column_list
        except Exception as e:
            #print(e)
            return []

    def check_answer(self, real, pred, gt_sql, db_id):
        if str(real).startswith('[Error]') or str(pred).startswith('[Error]'):
            return False
        if pred == "[['true']]":
            if real == "[['1.0']]":
                return True
            else:
                return False
        if pred == "[['false']]":
            if real == "[['0.0']]":
                return True
            else:
                return False
        if str(real) != 'null' and isinstance(real, str):
            real = eval(real)
        if str(pred) != 'null' and isinstance(pred, str):
            pred = eval(pred)
        
        
        is_count = 'count' in gt_sql.lower() # count( * )
        if is_count and pred=='[]':
            pred = [['0.0']]
        is_count = re.search(r'\bcount\s*\([^)]*\)\s*>\s*0\s*from\b', gt_sql.lower()) # count( * ) > 0 
        if is_count:
            pred = [[r] for r in np.unique(pred)]
            if pred == [['None']]:
                pred = [['0.0']]
            elif pred != [['0.0']]:
                pred = [['1.0']]
        if 'AVG' in gt_sql and 'CASE' in gt_sql: # calculating survival rate
            try: # 100.0 => 1.0
                converted = float(pred[0][0])
                if converted > 1.0:
                    pred = [[str(round(converted/100, 3))]]
            except:
                pass
        exec_acc = (real == pred)
        return exec_acc

    def execute(self, db_id:str, sql:str, is_gold_sql:bool, timeout:int=60):
        """
        Execute SQL after processing it.
        Processing is a bit different for gold SQL and pred SQL.
        Answer is also processed for easy comparison between executions.

        Args:
            sql (str): predicted SQL query
            is_gold_sql (bool): Whether the SQL query is gold SQL query or not.

        Returns:
            execution_result (str? list? not sure): the execution result.
        """
        if self.dataset != "bird":
            assert os.path.exists(f"{self.data_dir}/{self.dataset}/{db_id}.sqlite"), f"Database file does not exist: {self.data_dir}/{self.dataset}/{db_id}.sqlite"
            if is_gold_sql:
                processed_sql = postprocess_gt(sql, db_id=db_id)
            else:
                processed_sql = postprocess_pred(sql, db_id=db_id)
        else:
            assert os.path.exists(f"{self.data_dir}/{db_id}/{db_id}.sqlite"), f"Database file does not exist: {self.data_dir}/{db_id}/{db_id}.sqlite"
            processed_sql = sql

        if processed_sql == 'null':
            return 'null'
        else:
            try:
                if self.dataset != "bird":
                    execution_result = func_timeout(timeout=timeout,
                                                    func=execute_sql_for_evaluator,
                                                    args=(processed_sql, f"{self.data_dir}/{self.dataset}/{db_id}.sqlite"))
                else:
                    execution_result = func_timeout(timeout=timeout,
                                                    func=execute_sql_for_evaluator,
                                                    args=(processed_sql, f"{self.data_dir}/{db_id}/{db_id}.sqlite"))
                execution_result = process_answer(execution_result, db_id=db_id)
            except FunctionTimedOut:
                execution_result = f"[Error] Timeout in executing SQL: {timeout} sec\nSQL: {processed_sql}\n"
            except Exception as e:
                execution_result = f"[Error] Error in executing SQL: {e}\nSQL: {processed_sql}\n"
            return execution_result

    def __call__(self, db_id:str, pred_sql:str, gold_sql:str):
        """
        Checks if the predicted SQL is a false positive.
        """
        pred_sql = modify_distinct(pred_sql, gold_sql)
        pred_answer = self.execute(db_id, pred_sql, is_gold_sql=False)
        
        gold_answer = self.execute(db_id, gold_sql, is_gold_sql=True)
        is_correct = self.check_answer(gold_answer, pred_answer, gold_sql, db_id)
        result = {
            "pred_answer": pred_answer,
            "gold_answer": gold_answer,
            "is_correct": is_correct,
        }
        return result