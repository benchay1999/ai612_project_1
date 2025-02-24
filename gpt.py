import os
import json
import pandas as pd
from tqdm import tqdm

# Directory paths for database, results and scoring program
DB_ID = 'mimic_iv'
BASE_DATA_DIR = 'data'
RESULT_DIR = 'results'
SCORING_DIR = 'scoring'
TABLES_PATH = os.path.join('database', 'tables.json')               # JSON containing database schema
VALID_DATA_PATH = os.path.join(BASE_DATA_DIR, 'valid_data.json')
VALID_LABEL_PATH = os.path.join(BASE_DATA_DIR, 'valid_label.json')    # JSON file for validation data
DB_PATH = os.path.join('data', DB_ID, f'{DB_ID}.sqlite')               # Database path

assumptions = open("database/mimic_iv_assumption.txt", "r").read()

# Load data
with open(os.path.join(VALID_DATA_PATH), 'r') as f:
    valid_data = json.load(f)

with open(os.path.join(VALID_LABEL_PATH), 'r') as f:
    valid_labels = json.load(f)

def load_schema(DATASET_JSON):
    schema_df = pd.read_json(DATASET_JSON)
    schema_df = schema_df.drop(['column_names','table_names'], axis=1)
    schema = []
    f_keys = []
    p_keys = []
    for index, row in schema_df.iterrows():
        tables = row['table_names_original']
        col_names = row['column_names_original']
        col_types = row['column_types']
        foreign_keys = row['foreign_keys']
        primary_keys = row['primary_keys']
        for col, col_type in zip(col_names, col_types):
            index, col_name = col
            if index > -1:
                schema.append([row['db_id'], tables[index], col_name, col_type])
        for primary_key in primary_keys:
            index, column = col_names[primary_key]
            p_keys.append([row['db_id'], tables[index], column])
        for foreign_key in foreign_keys:
            first, second = foreign_key
            first_index, first_column = col_names[first]
            second_index, second_column = col_names[second]
            f_keys.append([row['db_id'], tables[first_index], tables[second_index], first_column, second_column])
    db_schema = pd.DataFrame(schema, columns=['Database name', 'Table Name', 'Field Name', 'Type'])
    primary_key = pd.DataFrame(p_keys, columns=['Database name', 'Table Name', 'Primary Key'])
    foreign_key = pd.DataFrame(f_keys,
                        columns=['Database name', 'First Table Name', 'Second Table Name', 'First Table Foreign Key',
                                 'Second Table Foreign Key'])
    return db_schema, primary_key, foreign_key

# Generates a string representation of foreign key relationships in a MySQL-like format for a specific database.
def find_foreign_keys_MYSQL_like(foreign, db_id):
    df = foreign[foreign['Database name'] == db_id]
    output = "["
    for index, row in df.iterrows():
        output += row['First Table Name'] + '.' + row['First Table Foreign Key'] + " = " + row['Second Table Name'] + '.' + row['Second Table Foreign Key'] + ', '
    output = output[:-2] + "]"
    if len(output)==1:
        output = '[]'
    return output

# Creates a string representation of the fields (columns) in each table of a specific database, formatted in a MySQL-like syntax.
def find_fields_MYSQL_like(db_schema, db_id):
    df = db_schema[db_schema['Database name'] == db_id]
    df = df.groupby('Table Name')
    output = ""
    for name, group in df:
        output += "Table " +name+ ', columns = ['
        for index, row in group.iterrows():
            output += row["Field Name"]+', '
        output = output[:-2]
        output += "]\n"
    return output

# Generates a comprehensive textual prompt describing the database schema, including tables, columns, and foreign key relationships.
def create_schema_prompt(db_id, db_schema, primary_key, foreign_key, is_lower=True):
    prompt = find_fields_MYSQL_like(db_schema, db_id)
    prompt += "Foreign_keys = " + find_foreign_keys_MYSQL_like(foreign_key, db_id)
    if is_lower:
        prompt = prompt.lower()
    prompt += "\nSQL Assumptions that you must follow:\n" + assumptions
    return prompt
    
from utils import read_json as read_data

db_schema, primary_key, foreign_key = load_schema(TABLES_PATH)

valid_data = read_data(VALID_DATA_PATH)

table_prompt = create_schema_prompt(DB_ID, db_schema, primary_key, foreign_key)

print(valid_data.keys())
print(valid_labels[list(valid_labels.keys())[0]])

import os
import re
import json

import openai
from openai import OpenAI
api_path = 'sample_submission_chatgpt_api_key.json'
with open(api_path, 'r') as f:
    json_data = json.load(f)
client = OpenAI(api_key=json_data['key'])

def post_process(answer):
    answer = answer.replace('\n', ' ')
    answer = re.sub('[ ]+', ' ', answer)
    answer = answer.replace("```sql", "").replace("```", "").strip()
    return answer

class Model():
    def __init__(self):
        current_real_dir = os.getcwd()
        # current_real_dir = os.path.dirname(os.path.realpath(__file__))
        target_dir = os.path.join(current_real_dir, 'sample_submission_chatgpt_api_key.json')

        if os.path.isfile(target_dir):
            with open(target_dir, 'rb') as f:
                openai.api_key = json.load(f)['key']
        if not os.path.isfile(target_dir) or openai.api_key == "":
            raise Exception("Error: no API key file found.")

    def ask_chatgpt(self, prompt, model="gpt-4o-mini", temperature=0.0):
        response = client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    messages=prompt
                )
        return response.choices[0].message.content

    def generate(self, input_data):
        """
        Arguments:
            input_data: list of python dictionaries containing 'id' and 'input'
        Returns:
            labels: python dictionary containing sql prediction or 'null' values associated with ids
        """

        labels = {}

        for sample in tqdm(input_data):
            answer = self.ask_chatgpt(sample['input'])
            labels[sample["id"]] = post_process(answer)

        return labels

myModel = Model()
data = valid_data["data"]
system_msg = "Given the following SQL tables and SQL assumptions you must follow, your job is to write queries given a user’s request.\n IMPORTANT: If you think you cannot predict the SQL accurately, you must answer with 'null'."
input_data = []
for sample in data:
    sample_dict = {}
    sample_dict['id'] = sample['id']
    conversation = [{"role": "system", "content": system_msg + '\n\n' + table_prompt}]
    user_question_wrapper = lambda question: '\n\n' + f"""NLQ: \"{question}\"\nSQL: """
    conversation.append({"role": "user", "content": user_question_wrapper(sample['question'])})
    sample_dict['input'] = conversation
    input_data.append(sample_dict)

label_y = myModel.generate(input_data)

from utils import write_json as write_label

# Save the filtered predictions to a JSON file
os.makedirs(RESULT_DIR, exist_ok=True)
SCORING_OUTPUT_DIR = os.path.join(RESULT_DIR, 'prediction.json')
write_label(SCORING_OUTPUT_DIR, label_y)