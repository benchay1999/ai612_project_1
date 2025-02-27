# AI612 Project 1: Single-turn Text-to-SQL with Abstention

Your task is to develop a single-turn text-to-SQL model for an EHR database, specifically [MIMIC-IV Demo](https://physionet.org/content/mimic-iv-demo/2.2/). From a natural language question, the model should either – (A) generate an accurate SQL query; or (B) abstain from generating a SQL query (i.e., output “null” in string format) when uncertain of its correctness – within a single interaction between the user and the model.

The scope of the input questions that a user can ask includes [diverse topics relevant to clinical settings](https://github.com/glee4810/EHRSQL) (e.g., patient demographics, vital signs, and disease survival rates), as well as questions that are not answerable. Questions those are not answerable include, but not limited to: (1) questions that are not answerable given the database schema (e.g., asking about today's weather) or SQL functionalities (e.g.,  drawing a plot); or (2) ambiguous questions that require further clarifications through additional interactions between the user and the model (e.g., “How many patients were in severe conditions last year?”). Note that every question that is not answerable does not have a corresponding SQL query, and the model should abstain from generating such.

Check [Project 1 Specs](https://docs.google.com/document/d/1CghIWzaSvuqgQVzCVLAUOOPiBED-zXogUdm0Bzvk-Cs/edit?usp=sharing) for more details.

## Database
We use the [MIMIC-IV database demo](https://physionet.org/content/mimic-iv-demo/2.2/), which anyone can access the files as long as they conform to the terms of the [Open Data Commons Open Database License v1.0](https://physionet.org/content/mimic-iv-demo/view-license/2.2/).

## Tutorials
Check out the jupyter notebook files in the [`example_baselines/`](example_baselines/).

Especially, the [`gpt_4o_mini.ipynb`](example_baselines/gpt_4o_mini.ipynb) would be a good starting point to your implementation.

Colab version of the baselines are also available:
- [`dummy.ipynb`](https://colab.research.google.com/drive/1dkgNR3Qi5ZrtzX_QJbQNhXLpyKHxgq-h?usp=sharing)
- [`gpt_4o_mini.ipynb`](https://colab.research.google.com/drive/1IQIOHrl-4sgorbtFZFVP2NnUP_7XdjmZ?usp=sharing)


## Dependencies
The codes were tested in Colab and in a local environment (Python 3.11) with the dependecies listed in `requirements.txt`.

### Colab
Install func_timeout using `pip install func-timeout`

### Local
```bash
conda create -n ai612-project1 python=3.11 -y
conda activate ai612-project1
pip install -r requirements.txt
```