# AI612 Project 1: Single-turn Text-to-SQL with Abstention

Check Project 1 Specs for more details.

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